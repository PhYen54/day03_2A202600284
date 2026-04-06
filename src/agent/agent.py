import os
import re
import json
import time
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker
from src.telemetry.langsmith_tracer import langsmith_tracer

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )

        return f"""
        You are a ReAct Agent designed to solve multi-step reasoning tasks using specific tools.
        You are a shopping assistant, not a conversational chatbot.

        AVAILABLE TOOLS:
        {tool_descriptions}

        CORE TASK:
        Find a combination of EXACTLY 1 laptop, 1 keyboard, and 1 mouse satisfying:
        - Total Net Price (Final Price after discount) <= Budget.
        - Total Performance >= Required Threshold.
        - All items MUST have Stock > 0.

        STRICT RE-ACT FORMAT:
        Thought: (Reasoning about what information you need and which tool to use)
        Action: tool_name(arguments)
        Observation: (STOP! Do NOT write anything after 'Action'. Wait for the system response.)

        --- RE-ACT LOOP RULES ---
        1. Write ONLY ONE 'Thought' and ONE 'Action' at a time.
        2. Arguments for tools must be strings (e.g., Action: get_products_by_category("laptop")).
        3. Do NOT hallucinate data. Only use information returned in 'Observation'.
        4. If you have found a valid combo, use 'validate_combination' to confirm before giving the Final Answer.

        STRICT CONSTRAINTS & PROCESS:
        - STEP 1: Use 'get_products_by_category' for "laptop", "keyboard", and "mouse" to gather candidates.
        - STEP 2: Manually pick 3 items that fit the budget and performance.
        - STEP 3: Use 'validate_combination("ID1, ID2, ID3")' to get the final bill and stock check.
        - STEP 4: Provide the 'Final Answer' with the detailed bill.

        - NO markdown (no **bold**, no ###), NO code blocks (no ```).
        - If no valid combination exists after checking all options, state it clearly in Final Answer.

        EXAMPLE TURN:
        Thought: I need to see available laptops to start building the combo.
        Action: get_products_by_category("laptop")
             """
    def run(self, user_input: str) -> str:
        """
        Enhanced ReAct loop with comprehensive logging for metrics, traces, and failure analysis.
        """
        start_time = time.time()
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        root_span = langsmith_tracer.start_agent_run(user_input, self.llm.model_name, self.max_steps)
        
        # Execution trace
        execution_trace = {
            "input": user_input,
            "model": self.llm.model_name,
            "steps": [],
            "final_answer": None,
            "termination_reason": None,
            "total_time_ms": 0
        }
        
        # Lịch sử hội thoại để gửi lại cho LLM (bao gồm Thought, Action, Observation)
        history = f"Question: {user_input}\n"
        system_prompt = self.get_system_prompt()
        steps = 0
        total_latency = 0
       
        while steps < self.max_steps:
            step_start = time.time()
            step_span = root_span.start_child(
                name=f"react_step_{steps + 1}",
                run_type="llm",
                inputs={"history": history},
                metadata={"step": steps + 1},
            )
            response = self.llm.generate(history, system_prompt=system_prompt)
            step_end = time.time()
            step_latency = int((step_end - step_start) * 1000)
            total_latency += step_latency
            
            # Track metrics
            tracker.track_request(response.get('provider', 'unknown'), self.llm.model_name, response.get('usage', {}), step_latency)
            
            result = response['content'] if isinstance(response, dict) else response
            print(f"--- Step {steps+1} LLM OUTPUT ---\n", result)
            step_span.end(
                outputs={
                    "thought_action": result,
                    "latency_ms": step_latency,
                    "usage": response.get('usage', {}) if isinstance(response, dict) else {},
                }
            )

            # Add to trace
            execution_trace["steps"].append({
                "step": steps + 1,
                "thought_action": result,
                "latency_ms": step_latency,
                "usage": response.get('usage', {})
            })

            #  Nếu có Final Answer → kết thúc
            if "Final Answer:" in result:
                end_time = time.time()
                total_time_ms = int((end_time - start_time) * 1000)
                execution_trace["final_answer"] = result.split("Final Answer:")[-1].strip()
                execution_trace["termination_reason"] = "success"
                execution_trace["total_time_ms"] = total_time_ms
                execution_trace["loop_count"] = steps + 1
                execution_trace["total_latency_ms"] = total_latency
                
                logger.log_event("AGENT_END", {
                    "steps": steps + 1, 
                    "termination_quality": "success",
                    "total_time_ms": total_time_ms,
                    "total_latency_ms": total_latency
                })
                
                # Save trace
                self._save_execution_trace(execution_trace)
                root_span.end(
                    outputs={
                        "termination_reason": "success",
                        "final_answer": execution_trace["final_answer"],
                        "steps": steps + 1,
                        "total_time_ms": total_time_ms,
                    }
                )
                return execution_trace["final_answer"]
            
            action_match = re.search(r"Action:\s*(\w+)\((.*)\)", result)

            if action_match:
                tool_name = action_match.group(1)
                args_str = action_match.group(2)

                observation = self._execute_tool(tool_name, args_str, root_span, steps + 1)
                print(f"--- Observation ---\n", observation)

                # Add observation to trace
                execution_trace["steps"][-1]["observation"] = observation

                history += f"\n{result}\nObservation: {observation}\n"
            else:
                # Parser error
                logger.log_event("PARSER_ERROR", {"step": steps + 1, "output": result})
                observation = "Error: Invalid action format. Please provide Action: tool_name(arguments)"
                execution_trace["steps"][-1]["observation"] = observation
                history += f"\n{result}\nObservation: {observation}\n"

            steps += 1

        # Timeout
        end_time = time.time()
        total_time_ms = int((end_time - start_time) * 1000)
        execution_trace["termination_reason"] = "timeout"
        execution_trace["total_time_ms"] = total_time_ms
        execution_trace["loop_count"] = steps
        execution_trace["total_latency_ms"] = total_latency
        
        logger.log_event("AGENT_END", {
            "steps": steps, 
            "termination_quality": "timeout",
            "total_time_ms": total_time_ms,
            "total_latency_ms": total_latency
        })
        
        # Save trace
        self._save_execution_trace(execution_trace)
        root_span.end(
            outputs={
                "termination_reason": "timeout",
                "steps": steps,
                "total_time_ms": total_time_ms,
            }
        )
        return "Max steps reached without final answer."
    def _execute_tool(self, tool_name: str, args_str: str, root_span: Any = None, step: Optional[int] = None) -> str:
        tool_span = root_span.start_child(
            name=f"tool_{tool_name}",
            run_type="tool",
            inputs={"raw_args": args_str},
            metadata={"step": step},
        ) if root_span else None

        try:
            tool_dict = next((t for t in self.tools if t['name'] == tool_name), None)

            if not tool_dict:
                # Hallucination error
                logger.log_event("HALLUCINATION_ERROR", {"tool_name": tool_name, "available_tools": [t['name'] for t in self.tools]})
                err = f"Error: Tool '{tool_name}' not found. Available tools: {[t['name'] for t in self.tools]}"
                if tool_span:
                    tool_span.end(outputs={"observation": err}, error=err)
                return err
            
            tool_func = tool_dict['func'] 
            clean_args = args_str.strip().strip('"').strip("'").strip(")")
            observation = tool_func(clean_args)
            if tool_span:
                tool_span.end(outputs={"args": clean_args, "observation": observation})
            return observation
        
        except Exception as e:
            logger.log_event("TOOL_EXECUTION_ERROR", {"tool_name": tool_name, "args": args_str, "error": str(e)})
            error_message = f"Error executing tool: {str(e)}"
            if tool_span:
                tool_span.end(outputs={"observation": error_message}, error=str(e))
            return error_message
    
    def _save_execution_trace(self, trace: Dict[str, Any]):
        """Save execution trace to logs/ directory as JSON."""
        os.makedirs("logs", exist_ok=True)
        timestamp = int(time.time())
        filename = f"logs/trace_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(trace, f, indent=2, ensure_ascii=False)
        logger.log_event("TRACE_SAVED", {"filename": filename})
    
