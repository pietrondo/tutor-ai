# ZAI Model API Integration

This document describes the integration of ZAI Model API (GLM models) into the Tutor AI application, providing advanced AI capabilities including agent-powered slide generation.

## Overview

The ZAI integration adds support for GLM (General Language Model) models from ZAI, featuring:

- **GLM-4.6**: Flagship model with advanced reasoning and agent capabilities
- **GLM-4.5**: Advanced model for complex tasks
- **GLM-4.5V**: Vision-capable model for image analysis
- **GLM-4.5 Air**: Optimized model for performance and cost
- **GLM-4**: Standard model for general tasks
- **GLM-4.1V**: Vision model with visual analysis capabilities

## Features

### 1. Multi-Provider Support
- Seamless integration with existing OpenAI and local LLM providers
- Dynamic model selection based on task type and budget
- Automatic fallback mechanisms

### 2. Agent-Powered Slide Generation
- Advanced AI agents for creating comprehensive presentations
- Structured content generation with visual elements
- Academic-level content with presenter notes
- Multiple slide types (title, content, bullet, image, quote)

### 3. Enhanced Capabilities
- **Thinking Mode**: Step-by-step reasoning for complex tasks
- **Agent Tasks**: Advanced agentic capabilities for slide creation
- **Context Window**: Up to 200K tokens for large document processing
- **Cost Optimization**: Competitive pricing with budget controls

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# ZAI Model API Configuration
ZAI_API_KEY=your_zai_api_key_here
ZAI_MODEL=glm-4.5
ZAI_BASE_URL=https://api.z.ai/api/paas/v4

# LLM Service Configuration
LLM_TYPE=zai
BUDGET_MODE=false
```

### Setup Instructions

1. **Get ZAI API Key**:
   - Visit [ZAI Platform](https://z.ai)
   - Sign up for an account
   - Generate an API key from the dashboard
   - Add the key to your `.env` file

2. **Configure Model Type**:
   ```bash
   LLM_TYPE=zai
   ```

3. **Optional: Test Connection**:
   ```python
   from services.llm_service import LLMService

   llm_service = LLMService()
   status = await llm_service.test_zai_connection()
   print(status)
   ```

## Model Selection

### Automatic Selection

The system automatically selects the best model based on task type:

- **Slide Creation**: GLM-4.6 (best for agentic tasks)
- **Complex Reasoning**: GLM-4.6
- **Study Plans**: GLM-4.5
- **Content Analysis**: GLM-4.5
- **Quiz Generation**: GLM-4.5 Air (budget-friendly)
- **General Chat**: GLM-4.5

### Manual Selection

You can manually specify a model:

```python
llm_service = LLMService()
await llm_service.set_model("glm-4.6")
```

## Usage Examples

### 1. Basic Chat with ZAI

```python
from services.llm_service import LLMService

llm_service = LLMService()
response = await llm_service.generate_response(
    query="Explain quantum computing",
    context={"text": "Context from your documents"},
    course_id="physics-101"
)
```

### 2. Generate Quiz with ZAI

```python
quiz = await llm_service.generate_quiz(
    course_id="computer-science-101",
    topic="Algorithms",
    difficulty="medium",
    num_questions=5
)
```

### 3. Agent-Powered Slide Generation

```python
slides = await llm_service.generate_slides_with_zai_agent(
    course_id="mathematics-201",
    topic="Linear Algebra",
    num_slides=12,
    slide_style="academic",
    audience="university"
)
```

## API Endpoints

### ZAI Slide Generation

```http
POST /generate-slides/zai-agent
Content-Type: application/json

{
  "course_id": "course-123",
  "topic": "Machine Learning Fundamentals",
  "num_slides": 10,
  "slide_style": "modern",
  "audience": "university"
}
```

### ZAI Status Check

```http
GET /generate-slides/zai-status
```

Response:
```json
{
  "zai_available": true,
  "current_model_type": "zai",
  "connection_status": {
    "connected": true,
    "provider": "zai",
    "url": "https://api.z.ai/api/paas/v4",
    "available_models": ["glm-4.6", "glm-4.5", "glm-4.5v", "glm-4.5-air", "glm-4", "glm-4.1v"]
  },
  "current_model": "glm-4.5",
  "agent_capabilities": {
    "slide_creation": true,
    "thinking_mode": true,
    "advanced_reasoning": true
  }
}
```

## Frontend Integration

### Model Manager Component

The ModelManager component now supports ZAI models with:

- Real-time connection status
- Model selection interface
- Agent capabilities display
- Connection testing functionality

### ZAI Slide Generator

A dedicated component for ZAI-powered slide generation featuring:

- Interactive configuration interface
- Real-time slide preview
- Multiple presentation themes
- Export functionality

### Mode Selection

Users can choose between:

- **Standard AI**: Traditional slide generation based on course materials
- **ZAI Agent**: Advanced agent-powered generation with enhanced capabilities

## Model Capabilities

### GLM-4.6 (Premium)
- **Context Window**: 200K tokens
- **Max Tokens**: 8,192
- **Features**: Thinking mode, advanced reasoning, agent tasks
- **Use Cases**: Complex reasoning, coding, study plans, slide creation
- **Cost**: Most expensive

### GLM-4.5 (Advanced)
- **Context Window**: 128K tokens
- **Max Tokens**: 4,096
- **Features**: Advanced reasoning, agent support
- **Use Cases**: Study plans, content analysis, slide creation
- **Cost**: Mid-range

### GLM-4.5V (Vision)
- **Context Window**: 128K tokens
- **Max Tokens**: 4,096
- **Features**: Visual analysis, image processing
- **Use Cases**: Document analysis, visual content
- **Cost**: Mid-range

### GLM-4.5 Air (Optimized)
- **Context Window**: 128K tokens
- **Max Tokens**: 4,096
- **Features**: Performance optimized
- **Use Cases**: Chat, quiz, quick responses
- **Cost**: Budget-friendly

### GLM-4 (Standard)
- **Context Window**: 128K tokens
- **Max Tokens**: 4,096
- **Features**: General purpose
- **Use Cases**: Chat, basic analysis
- **Cost**: Low

### GLM-4.1V (Vision Standard)
- **Context Window**: 128K tokens
- **Max Tokens**: 4,096
- **Features**: Basic visual analysis
- **Use Cases**: Simple image analysis
- **Cost**: Low

## Error Handling

The integration includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Graceful handling with user-friendly messages
- **API Errors**: Fallback to alternative providers when possible
- **Validation**: Input validation and sanitization

## Monitoring and Logging

All ZAI API calls are logged with:

- Model usage statistics
- Token consumption tracking
- Cost estimation
- Performance metrics
- Error details

## Security

- API keys are stored securely in environment variables
- Request validation and sanitization
- Rate limiting and quota management
- Error information sanitization (no sensitive data exposure)

## Troubleshooting

### Common Issues

1. **API Key Not Found**:
   - Ensure `ZAI_API_KEY` is set in `.env`
   - Verify the API key is valid and active

2. **Connection Failed**:
   - Check internet connectivity
   - Verify the API endpoint URL
   - Test with the status endpoint

3. **Model Not Available**:
   - Check model availability with status endpoint
   - Verify model name spelling
   - Use fallback models if needed

4. **High Latency**:
   - Try using GLM-4.5 Air for faster responses
   - Reduce context size
   - Enable budget mode for cost optimization

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Planned improvements include:

- Streaming support for real-time responses
- Additional vision model capabilities
- Custom agent training
- Advanced analytics and usage tracking
- Multi-modal content generation

## Support

For issues related to:
- **ZAI API**: Contact ZAI support
- **Integration**: Check GitHub issues
- **Documentation**: Update this README with improvements

## License

This integration follows the same license as the main Tutor AI project.