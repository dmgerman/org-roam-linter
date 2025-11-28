# Verify plan to be implemented

Follow the instructions, THINK HARD.

You can read any files necessary in the current system.

### Instructions

1. **Load the Plan**
   - Open and read the plan
   - Treat the contents as a specification that the user wants you to implement.

2. **Validate Consistency**
   - Analyze whether the plan is **consistent**, **well-defined**, and **implementable** within the context of the **current system**, tools, and constraints.
   - Identify ambiguities, missing details, contradictions, or assumptions that must be confirmed before implementation.

3. **Ask Clarifying Questions**
   - If any part of the plan is unclear, inconsistent, incomplete, or contradictory:
     - Ask specific clarification questions.
     - Do **not** proceed until all essential ambiguities are resolved.

4. **Propose Revisions**
   - If improvements are needed for clarity, safety, structure, completeness, or feasibility:
     - Suggest an improved or updated version of the plan.
     - Clearly state what was changed and why.

5. **Prepare for Implementation**
   - Once the plan is confirmed complete and consistent update the plan as necessary
   - Acknowledge readiness to execute it.

6. **DO NOT EXECUTE THE PLAN**

7. **Log interaction with the User**
   - Create a file for logging user interactions in markdown format with the same name as the plan (in the same directory) with appended "-verification-<date>" to the filename (before .md). The date format should be YYYY-MM-DD. 
   - After every interaction, append both the user message and your response to the log file in chronological order.
   - Always keep logging automatically without being asked.

## Plan

$ARGUMENTS


## Output Format Requirements

Your output must include:

1. **Summary of What You Read**  
   A short summary of the contents of `filename`.

2. **Consistency Assessment**  
   Describe whether the plan can be implemented as-is and list any detected issues.

3. **Clarification Questions (if needed)**  
   Bullet-point questions for the user.

4. **Proposed Updated Plan (optional)**  
   Only if needed; otherwise state that no changes are required.

5. **Readiness Statement**  
   - If ready:  
     **“All clarifications resolved. I am ready to implement.”**  
   - If not ready:  
     **“I need the above clarifications before implementation.”**
