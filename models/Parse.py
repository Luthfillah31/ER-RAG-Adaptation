import re

def execute_api_chain(dsl_command_block: str, api_client) -> str:
    # --- NEW: Extract only the content inside markdown code blocks ---
    code_match = re.search(r"```(?:python)?\s*(.*?)\s*```", dsl_command_block, re.DOTALL)
    if code_match:
        dsl_command_block = code_match.group(1)
        
    # Proceed with splitting the commands, but ignore comments
    raw_lines = [cmd.strip() for cmd in dsl_command_block.strip().split('\n') if cmd.strip()]
    commands = [line for line in raw_lines if not line.startswith('#')] # Ignore Python comments
    
    final_context = ""
    step_memory = {}
    
    for step_idx, dsl_command in enumerate(commands):
        step_num = step_idx + 1 # Index dimulai dari 1
        try:
            func_match = re.match(r"^\s*(\w+)\s*\(", dsl_command)
            if not func_match:
                print(f"[Parse Error] Invalid syntax in step {step_num}: {dsl_command}")
                return final_context
            
            func_name = func_match.group(1)
            args_matches = re.findall(r'(\w+)\s*=\s*"([^"]*)"', dsl_command)
            kwargs = {k: v for k, v in args_matches}
            
            # THE UPGRADED GRAPH JOIN: Ekstraksi Variabel Multi-Langkah
            for k, v in kwargs.items():
                # Mencari pola seperti {STEP1_id} atau {STEP2_projectID}
                match = re.search(r"\{STEP(\d+)_([a-zA-Z0-9_]+)\}", v)
                if match:
                    target_step = int(match.group(1))
                    extract_col = match.group(2)
                    
                    # Ambil memori dari langkah yang diminta
                    source_records = step_memory.get(target_step, [])
                    extracted_vals = [str(record.get(extract_col)) for record in source_records if record.get(extract_col) is not None]
                    kwargs[k] = ",".join(list(set(extracted_vals)))
                    
            print(f"[DEBUG Parse] Step {step_num}: Executing {func_name} with args {kwargs}")
            
            if not hasattr(api_client, func_name):
                print(f"[Parse Error] API Client has no function named: {func_name}")
                return final_context
                
            api_function = getattr(api_client, func_name)
            response_data = api_function(**kwargs)
            
            # --- SMART DATA CATCHER ---
            # Jika response dari API adalah Dictionary (seperti MySQL)
            if isinstance(response_data, dict):
                results = response_data.get('results', [])
            # Jika response dari API adalah List murni (seperti Wikibase terbaru)
            elif isinstance(response_data, list):
                results = response_data
            else:
                results = []
                
            # --- TAMBAHAN KEAMANAN (DEFENSIVE PROGRAMMING) ---
            if not isinstance(results, list):
                return final_context + f"\n[API Error] Step {step_num} gagal. Format data salah: {results}"
            
            # CEK KOSONG
            if not results:
                return final_context + f"\nNo records found at Step {step_num} ({func_name}). Chain aborted."
                
            # SIMPAN hasil pencarian ke memori langkah ini
            step_memory[step_num] = results
                
            # Verbalisasi data
            context_lines = [f"--- Step {step_num} ({func_name}) Results ---"]
            for index, record in enumerate(results):
                record_str = ", ".join([f"{k}: {v}" for k, v in record.items()])
                context_lines.append(f"Record {index + 1} -> {record_str}")
                
            final_context += "\n".join(context_lines) + "\n\n"
            
        except Exception as e:
            print(f"[Parse Error] Failed at step {step_num}: {e}")
            return final_context

    return final_context.strip()