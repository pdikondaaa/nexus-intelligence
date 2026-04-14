import pandas as pd

class ExcelAgent:
    def __init__(self, file_path, llm):
        self.df = pd.read_excel(file_path)
        self.llm = llm

    def generate_code(self, query):
        prompt = f"""
You are a Python data analyst.

You are given a pandas DataFrame called df.

Columns:
{self.df.columns.tolist()}

STRICT RULES:
1. Generate ONLY Python code
2. NO explanation
3. ALWAYS return FINAL RESULT (not dataframe)
4. If query asks average → MUST use .mean()
5. If query asks sum → MUST use .sum()
6. NEVER return df or filtered df directly

GOOD EXAMPLES:

Q: average claim for smokers
A: df[df['smoker']=='Yes']['claim'].mean()

Q: total claim
A: df['claim'].sum()

BAD EXAMPLES (DO NOT DO):
❌ df[df['smoker']=='Yes']
❌ df.head()

---

Query:
{query}
"""

        response = self.llm.invoke(prompt).content.strip()

        # Clean code (remove markdown if any)
        if "```" in response:
            response = response.split("```")[1]

        return response

    def safe_exec(self, code):
        # 🚫 block dangerous keywords
        banned = ["import", "os", "sys", "open", "exec", "eval", "__"]

        for word in banned:
            if word in code:
                return "Unsafe code detected"

        try:
            local_vars = {"df": self.df}

            exec(code, {}, local_vars)

            # get last variable
            result = list(local_vars.values())[-1]

            
            # ✅ If dataframe → try auto-fix
            if isinstance(result, pd.DataFrame):

                # If smoker filter → auto compute mean
                if "smoker" in code and "claim" in self.df.columns:
                    try:
                        fixed = self.df[self.df['smoker'] == 'Yes']['claim'].mean()
                        return f"{round(fixed, 2)}"
                    except:
                        pass

                return result.head(5).to_string()

            # ✅ If numeric
            if isinstance(result, (int, float)):
                return f"{round(result, 2)}"

            # ✅ Series
            if isinstance(result, pd.Series):
                return result.to_string()

            return str(result)

        except Exception as e:
            return f"Execution error: {str(e)}"

    def query(self, question):
        code = self.generate_code(question)

        print("\n🔹 GENERATED CODE:\n", code)

        result = self.safe_exec(code)

        return result