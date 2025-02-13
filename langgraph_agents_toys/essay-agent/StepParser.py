import streamlit as st



class StepParser:
    def __init__(self) -> None:
        pass
    def parse_and_display(self,data):
        with st.chat_message("assistant"):
            if 'planner' in data:
                self.handle_planner(data['planner'])
            elif 'research_plan' in data:
                self.handle_research_plan(data['research_plan'])
            elif 'reflect' in data:
                self.handle_reflect(data['reflect'])
            elif 'research_critique' in data:
                self.handle_research_critique(data['research_critique'])
            elif 'generate' in data:
                self.handle_generate(data['generate'])
            else:
                st.warning("Unsupported dictionary type provided.")

    def handle_planner(self,planner_data):
        """Handles the 'planner' type dictionary."""
        plan = planner_data.get('plan', 'No plan available')
        st.write("Understood! I will be the planner of the operation.")
        st.subheader('initial planning from Planner node')
        with st.popover("Planner"):
            st.write("**Plan Details:**")
            st.write(plan)
        

    def handle_research_plan(self,research_plan_data):
        """Handles the 'research_plan' type dictionary and iterates through its content."""
        content = research_plan_data.get('content', [])
        st.write("for this essay, a suitable research plan would include these key points")
        st.subheader("Research Plan Overview:")
        st.write(f"Total items in research plan: {len(content)}")
        with st.popover("Research Plan"):
            st.write("This step is from the **Research Plan**.")
            st.write("**Research Plan Details:**")
            
            # Iterate through each item in the content list
            for index, item in enumerate(content):
                st.write(f"**{index + 1}:**")
                st.write(item)
                st.write("---")  
        


    def handle_reflect(self,reflect_data):
        """Handles the 'reflect' type dictionary."""
        reflection = reflect_data.get('critique', 'No reflection available')
        st.write("I'm handing this to the reflection node, it'll reflect on the essay so far.")
        st.subheader("Reflection Overview:")
        with st.popover("Reflect"):
            st.write("This step is from the **Reflect**.")
            st.write("**Reflection Details:**")
            st.write(reflection)

    def handle_research_critique(self,research_critique_data):
        """Handles the 'research_critique' type dictionary."""
        critique = research_critique_data.get('content', [])
        st.write("I'm handing this to the research critique node, it'll critique the essay so far.")
        st.subheader("Research Critique Overview:")
        st.write(f"Total items in research critique: {len(critique)}")
        with st.popover("Research Critique"):
            st.write("This step is from the **Research Critique**.")
            st.write("**Critique Details:**")
            for index, item in enumerate(critique):
                st.write(f"**Item {index + 1}:**")
                st.write(item)
                st.write("---")  

    def handle_generate(self,generate_data):
        """Handles the 'generate' type dictionary."""
        generated_content = generate_data.get('draft', 'No content generated')
        st.subheader("""Here's your essay!""")
        st.write(generated_content)