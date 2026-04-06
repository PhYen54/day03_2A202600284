import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

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
        Sửa lỗi TypeError: lấy result['content'] và xử lý vòng lặp ReAct chuẩn.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        # Lịch sử hội thoại để gửi lại cho LLM (bao gồm Thought, Action, Observation)
        history = f"Question: {user_input}\n"
        system_prompt = self.get_system_prompt()
        steps = 0
       
        while steps < self.max_steps:
            response = self.llm.generate(history, system_prompt=system_prompt)
            result = response['content'] if isinstance(response, dict) else response
            print(f"--- Step {steps+1} LLM OUTPUT ---\n", result)

            #  Nếu có Final Answer → kết thúc
            if "Final Answer:" in result:
                logger.log_event("AGENT_END", {"steps": steps})
                return result.split("Final Answer:")[-1].strip()
            action_match = re.search(r"Action:\s*(\w+)\((.*)\)", result)

            if action_match:
                tool_name = action_match.group(1)
                args_str = action_match.group(2)

                observation = self._execute_tool(tool_name, args_str)
                print(f"--- Observation ---\n", observation)

                history += f"\n{result}\nObservation: {observation}\n"
            else:
                history += f"\n{result}\n(System Note: Please provide an Action or Final Answer.)\n"

            steps += 1

        logger.log_event("AGENT_END", {"steps": steps})
        return "Max steps reached without final answer."
    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        try:
            tool_dict = next((t for t in self.tools if t['name'] == tool_name), None)

            if not tool_dict:
                return f"Error: Tool '{tool_name}' not found."
            tool_func = tool_dict['func'] 
            clean_args = args_str.strip().strip('"').strip("'").strip(")")
            return tool_func(clean_args)
        
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
