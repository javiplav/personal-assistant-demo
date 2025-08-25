# 🎬 Demo Scripts: Enterprise AI Solutions Architect Demo

## 🎯 **Overview**

This folder contains demo scripts and materials for showcasing the enhanced personal assistant demo. These scripts are designed to demonstrate the enterprise capabilities of the AI assistant in live presentations and demonstrations.

---

## 📁 **Contents**

### **`demo_showcase.py`**
- **Purpose**: Automated demo script that runs through enterprise scenarios
- **Duration**: 5-7 minutes
- **Features**: Client management, meeting scheduling, task automation, business intelligence
- **Usage**: `python demo/demo_showcase.py`

---

## 🚀 **Demo Scenarios**

The automated demo script showcases:

### **1. Client Management (CRM)**
- Adding enterprise clients with project requirements
- Priority tracking and company information
- Client relationship management

### **2. Meeting Scheduling**
- Natural language meeting scheduling
- Duration and participant management
- Meeting scheduling

### **3. Task Management**
- Creating follow-up tasks
- Task automation and workflow management
- Priority and deadline tracking

### **4. Business Intelligence**
- Budget calculations and financial planning
- Percentage calculations for project planning
- ROI analysis and cost estimation

### **5. Multi-step Workflows**
- Complex business process orchestration
- Multi-tool integration and reasoning
- End-to-end workflow automation

---

## 🎬 **Demo Types**

### **Automated Demo (5-7 minutes)**
```bash
python demo/demo_showcase.py
```
- Runs through 6 predefined scenarios
- Interactive with user prompts
- Shows complete enterprise workflow

### **Manual Demo (Variable duration)**
```bash
# Individual commands for live demos
nat run --config_file configs/config-ollama.yml --input "Add client Microsoft with GPU cluster requirements, priority high"
nat run --config_file configs/config-ollama.yml --input "Schedule meeting with Microsoft team tomorrow at 2 PM for 90 minutes"
nat run --config_file configs/config-ollama.yml --input "Calculate 20% of 500000 for project budget"
```

### **Custom Demo Scenarios**
Use examples from `examples.md` to create custom demo scenarios based on your audience and requirements.

---

## 🎯 **Demo Preparation**

### **Before the Demo:**
1. **Test the script**: Run `python demo/demo_showcase.py` to ensure everything works
2. **Check configuration**: Verify your LLM provider is working
3. **Prepare backup**: Have manual commands ready in case of issues
4. **Practice**: Run through the demo multiple times

### **During the Demo:**
1. **Explain the context**: Set up the solutions architect scenario
2. **Highlight features**: Point out enterprise capabilities
3. **Show real value**: Emphasize time savings and business impact
4. **Engage audience**: Ask questions and encourage interaction

### **After the Demo:**
1. **Q&A**: Be ready for technical and business questions
2. **Follow-up**: Provide resources and next steps
3. **Feedback**: Collect input for improvements

---

## 🔧 **Technical Requirements**

### **Prerequisites:**
- NeMo Agent Toolkit installed and configured
- LLM provider set up (Ollama or NVIDIA NIM)
- Python environment activated
- Demo data cleared (optional, for fresh start)

### **Configuration:**
- Uses `configs/config-ollama.yml` by default
- Can be modified to use other configurations
- Supports both local and cloud LLM providers

---

## 📊 **Demo Metrics**

### **Success Indicators:**
- **Functionality**: All scenarios complete successfully
- **Performance**: Reasonable response times
- **Accuracy**: Correct data handling and calculations
- **Engagement**: Audience interest and questions

### **Common Issues:**
- **LLM connectivity**: Ensure Ollama is running or API keys are set
- **Data persistence**: Check that data files are writable
- **Configuration**: Verify config files are correct
- **Environment**: Ensure virtual environment is activated

---

## 🎯 **Customization**

### **Modifying Demo Scenarios:**
1. **Edit scenarios**: Modify the `demos` list in `demo_showcase.py`
2. **Add new features**: Include additional enterprise tools
3. **Change configuration**: Use different LLM providers
4. **Customize output**: Modify the display format

### **Creating New Demos:**
1. **Define purpose**: What should the demo showcase?
2. **Select scenarios**: Choose relevant enterprise features
3. **Write scripts**: Create new demo scripts
4. **Test thoroughly**: Ensure reliability and accuracy

---

## 🔗 **Related Files**

### **In Main Project:**
- **`docs/examples.md`**: Comprehensive examples for manual demos
- **`DEMO_VERIFICATION.md`**: Functionality verification (in this folder)
- **`README.md`**: Main project documentation
- **`configs/`**: Configuration files for different LLM providers

### **Configuration Options:**
- **`config-ollama.yml`**: Recommended for live demos
- **`config.yml`**: NVIDIA NIM for production demos
- **`config-ollama-env.yml`**: Flexible Ollama configuration

---

*These demo scripts provide a comprehensive way to showcase the enterprise AI assistant capabilities in live presentations and demonstrations.*
