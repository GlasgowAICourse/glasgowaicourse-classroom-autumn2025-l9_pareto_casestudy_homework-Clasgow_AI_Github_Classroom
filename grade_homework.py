import json
import nbformat
import subprocess
import sys
import re
import traceback

def execute_notebook(notebook_path):
    """
    Executes a Jupyter notebook by extracting its code and running it as a script.
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    except Exception as e:
        return None, f"Error reading notebook file: {e}"

    full_code = ""
    for cell in nb.cells:
        if cell.cell_type == 'code':
            # Remove the placeholder lines to prevent syntax errors
            clean_source = re.sub(r".*# YOUR CODE HERE.*", "1", cell.source)
            full_code += clean_source + '\n'

    if "n_subproblems = 1" in full_code:
        return None, "The GA parameters were not set. Please complete the configuration in the `run_moead_heatsink` function."

    try:
        process = subprocess.run(
            [sys.executable, '-c', full_code],
            capture_output=True,
            text=True,
            timeout=240  # 4-minute timeout
        )
        
        if process.returncode != 0:
            return None, f"Code execution failed with an error:\n{process.stderr}"
            
        return process.stdout, None
    except subprocess.TimeoutExpired:
        return None, "Code execution timed out after 4 minutes."
    except Exception as e:
        return None, f"An unexpected error occurred during execution: {e}"

def grade_result(output):
    """
    Parses the output to find the final ideal point and calculates a score.
    """
    if output is None:
        return 0, "Could not get output from the notebook."

    # The optimal value for the first objective (Thermal Resistance) from the solution
    OPTIMAL_F1 = 0.005
    TOLERANCE = 0.10  # 10% tolerance for full marks

    # Regex to find the *last* "Ideal point" line printed
    matches = re.findall(r"Ideal point: z = \[([0-9.]+),\s*([0-9.]+)\]", output, re.IGNORECASE)

    if not matches:
        return 0, "Could not find the 'Ideal point: z' in the output. Make sure the algorithm runs to completion."

    try:
        # Get the values from the last match found
        student_f1 = float(matches[-1][0])
    except (ValueError, IndexError):
        return 0, f"Could not parse the ideal point values from the output."

    # Calculate the absolute percentage error for the first objective
    error = abs(student_f1 - OPTIMAL_F1) / OPTIMAL_F1 if OPTIMAL_F1 != 0 else float('inf')

    score = 0
    if error <= TOLERANCE:
        score = 10.0
    elif error < 1.0: # Linear score decrease up to 100% error
        score = 10.0 * (1 - (error - TOLERANCE) / (1.0 - TOLERANCE))
    else:
        score = 0.0
    
    score = round(score, 2)
    
    feedback = (
        f"Grading based on the final Thermal Resistance (f1) in the ideal point.\n"
        f"Target f1: ~{OPTIMAL_F1:.3f}\n"
        f"Your Final f1: {student_f1:.3f}\n"
        f"Error: {error:.2%}\n"
        f"Score: {score}/10"
    )
    
    return score, feedback

def main():
    notebook_path = 'L9_Pareto_CaseStudy_Homework.ipynb'
    output, error_message = execute_notebook(notebook_path)

    if error_message:
        score = 0
        feedback = error_message
    else:
        score, feedback = grade_result(output)

    test_result = {
        'tests': [
            {
                'name': 'Heat Sink Multi-Objective Optimization',
                'score': score,
                'max_score': 10,
                'output': feedback,
            }
        ]
    }
    
    print(json.dumps(test_result))

if __name__ == "__main__":
    main()
