import re

def execute_api_chain(dsl_command_block: str, api_client) -> str:
    """
    Parses multi-line LLM-generated DSL commands and executes them sequentially.
    Handles in-memory JOINs by dynamically extracting any {PREVIOUS_columnName}.
    """
    commands = [cmd.strip() for cmd in dsl_command_block.strip().split('\n') if cmd.strip()]
    final_context = ""
    
    # Store the entire list of records from the previous step
    previous_results = [] 
    
    for step, dsl_command in enumerate(commands):
        try:
            func_match = re.match(r"^\s*(\w+)\s*\(", dsl_command)
            if not func_match:
                print(f"[Parse Error] Invalid syntax in step {step + 1}: {dsl_command}")
                return final_context
            
            func_name = func_match.group(1)
            args_matches = re.findall(r'(\w+)\s*=\s*"([^"]*)"', dsl_command)
            kwargs = {k: v for k, v in args_matches}
            
            # THE UPGRADED IN-MEMORY JOIN: Dynamic Attribute Extraction
            for k, v in kwargs.items():
                match = re.search(r"\{PREVIOUS_([a-zA-Z0-9_]+)\}", v)
                if match:
                    extract_col = match.group(1) # e.g., 'id' or 'projectID'
                    
                    if not previous_results:
                        return final_context + f"\n[Error] Step {step+1} requires {v} but no previous data exists."
                        
                    # Extract the requested column from ALL previous records
                    extracted_vals = [str(r[extract_col]) for r in previous_results if extract_col in r]
                    
                    if not extracted_vals:
                         return final_context + f"\n[Error] Column '{extract_col}' missing in previous results."
                         
                    # Deduplicate and apply Logical OR (comma separated)
                    kwargs[k] = ",".join(list(set(extracted_vals)))
            
            print(f"[DEBUG Parse] Step {step + 1}: Executing {func_name} with args {kwargs}")
            
            if not hasattr(api_client, func_name):
                print(f"[Parse Error] API Client has no function named: {func_name}")
                return final_context
                
            api_function = getattr(api_client, func_name)
            response_data = api_function(**kwargs)
            results = response_data.get('results', [])
            
            if not results:
                return final_context + f"\nNo records found at Step {step + 1} ({func_name}). Chain aborted."
                
            # SAVE the full result set for the next step to extract from
            previous_results = results
                
            # Verbalize this step's data
            context_lines = [f"--- Step {step + 1} ({func_name}) Results ---"]
            for index, record in enumerate(results):
                record_str = ", ".join([f"{k}: {v}" for k, v in record.items()])
                context_lines.append(f"Record {index + 1} -> {record_str}")
                
            final_context += "\n".join(context_lines) + "\n\n"
            
        except Exception as e:
            print(f"[Parse Error] Failed at step {step + 1}: {e}")
            return final_context

    print(f"[DEBUG Parse] Final Multi-Hop Context:\n{final_context}")
    return final_context.strip()