# Frontend Integration Guide

## 🎯 **How to Use Your Vapi Frontend with LangGraph Research Assistant**

Your Vapi frontend has been updated to support LangGraph Research Assistant configurations! Here's how to use it:

## 🚀 **Step-by-Step Setup**

### **1. Access the Agent Builder**
- Navigate to: `http://localhost:3000/agents` (or your frontend URL)
- You'll see the updated Agent Builder with new tabs

### **2. Choose Your Template**
Click on the **🚀 Templates** tab to see two options:

#### **🎙️ Voice-Optimized Research Assistant**
- **Best for**: Vapi voice calls
- **Response time**: 2-5 seconds
- **Cost**: LOW 💰 (~27% savings)
- **Features**: Immediate responses, voice-optimized, cost-efficient

#### **🔬 Full-Featured Research Assistant**
- **Best for**: Web interfaces, detailed research
- **Response time**: 30-60 seconds  
- **Cost**: HIGH 💰💰💰
- **Features**: Comprehensive research, multiple sources, detailed analysis

### **3. Load and Customize**
1. Click **"Load Template"** on your preferred option
2. The **📝 YAML Editor** tab will open with the pre-configured template
3. Customize the configuration if needed:
   - Change the assistant name
   - Modify the system prompt
   - Adjust voice settings
   - Update the ngrok URL if it changes

### **4. Test Your Configuration**
1. Click **"Test Config"** to validate the YAML
2. Switch to **🧪 Test Results** tab to see validation results
3. Fix any errors if they appear

### **5. Save and Deploy**
1. Click **"Save Agent"** to store your configuration
2. Your LangGraph Research Assistant is now ready for Vapi!

## 🔗 **Important URLs to Update**

### **Current ngrok URL (Update if it changes):**
```
https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app
```

### **If ngrok URL Changes:**
1. Get new URL: `curl -s http://localhost:4041/api/tunnels | grep public_url`
2. Update both templates in the frontend
3. Or manually edit the YAML in the editor

## 🎙️ **For Vapi Integration**

### **Webhook URL:**
```
https://1193-2603-8000-baf0-4690-14ce-4b1-5d2-9ea7.ngrok-free.app/vapi-webhook
```

### **Recommended Settings:**
- **Voice calls**: Use Voice-Optimized template
- **Web interface**: Use Full-Featured template
- **Cost optimization**: Always choose Voice-Optimized for Vapi

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Template not loading**
   - Refresh the page
   - Check browser console for errors

2. **YAML validation errors**
   - Check indentation (use spaces, not tabs)
   - Verify quotes are matched
   - Ensure proper YAML syntax

3. **ngrok URL not working**
   - Check if ngrok is still running
   - Get new URL and update templates
   - Restart ngrok if needed

4. **Save/Test not working**
   - Ensure backend is running on port 8000
   - Check network connectivity
   - Verify CORS settings

## 💡 **Pro Tips**

### **Cost Optimization:**
- Always use Voice-Optimized template for Vapi calls
- Save ~27% on voice call costs
- Use Full-Featured only for web interfaces

### **Quick Setup:**
1. Load Voice-Optimized template
2. Test configuration
3. Save agent
4. Use in Vapi immediately

### **Customization:**
- Modify system prompts for specific use cases
- Adjust response templates for your brand
- Change voice settings as needed

## 📊 **Template Comparison**

| Feature | Voice-Optimized | Full-Featured |
|---------|----------------|---------------|
| Response Time | 2-5 seconds | 30-60 seconds |
| Cost | LOW 💰 | HIGH 💰💰💰 |
| Research Depth | Quick summary | Comprehensive |
| Sources | 1-2 sources | Up to 10 sources |
| Content Length | Short | Short/Medium/Long |
| Best For | Voice calls | Web interfaces |

## 🎉 **You're Ready!**

Your frontend now supports both:
- ✅ **Tesseract Engine** (workflow automation)
- ✅ **LangGraph Research Assistant** (research & content)

Choose the right template for your use case and enjoy immediate, cost-effective AI assistance! 