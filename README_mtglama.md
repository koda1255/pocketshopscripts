# MTG Lama - AI Assistant for Magic: The Gathering

## Overview
`mtgLama.py` is an advanced AI assistant specifically designed for Magic: The Gathering card shop operations. It combines multiple specialized tools and functions to provide comprehensive support for card identification, pricing, market analysis, and general MTG assistance.

## Features

### 🤖 Core AI Assistant
- **Conversational Interface**: Natural language interaction with AI model
- **Function Calling**: Automatic detection and execution of specialized functions
- **Context Awareness**: Maintains conversation history and context
- **Multi-Modal Support**: Handles text, image paths, and structured queries

### 🔧 Integrated Functions

#### 1. DateTime Function
- **Current Time Information**: Provides detailed date and time data
- **Multiple Formats**: ISO, readable, short, long, and component formats
- **Timezone Support**: Local timezone handling
- **Knowledge Cutoff**: Tracks AI model knowledge limitations

#### 2. Card Price Lookup
- **Real-Time Pricing**: Fetches current MTG card prices
- **Multiple Sources**: Integrates with price databases
- **Price History**: Access to historical price data
- **Market Analysis**: Price trends and market insights

#### 3. Card Image Identification
- **Visual Recognition**: Identifies cards from image files
- **Multiple Formats**: Supports JPG, PNG, and other image formats
- **Automatic Detection**: Processes image paths in conversation
- **Detailed Results**: Provides card name, set, and additional information

#### 4. Web Search Integration
- **Current Information**: Searches for latest MTG news and updates
- **Brave Search**: Uses Brave search engine for comprehensive results
- **Query Processing**: Handles complex search queries
- **Result Summarization**: AI-powered summary of search results

#### 5. Trend/News Collector
- **MTG News**: Specialized Magic: The Gathering news collection
- **Market Trends**: Financial and market trend analysis
- **Article Summarization**: Condenses news articles for quick reading
- **Real-Time Updates**: Current market and community information

#### 6. Cost-to-Value Search
- **Investment Analysis**: Evaluates MTG product investments
- **Box Set Analysis**: Analyzes sealed product value propositions
- **ROI Calculations**: Return on investment assessments
- **Market Comparisons**: Compares different product values

### 🧠 AI Model Integration
- **Ollama Integration**: Uses local Ollama AI models
- **Hermes3 Model**: Optimized for MTG knowledge and assistance
- **Streaming Responses**: Real-time response generation
- **Context Management**: Maintains conversation context across sessions

### 💾 Data Persistence
- **ChromaDB Integration**: Vector database for conversation history
- **Context Retrieval**: Searches past conversations for relevance
- **Memory Management**: Efficient storage and retrieval of chat history
- **Persistent Storage**: Maintains data across sessions

## Installation

### Prerequisites
```bash
pip install ollama
pip install chromadb
pip install requests
```

### Required Dependencies
- **Ollama**: Local AI model server
- **ChromaDB**: Vector database for conversation history
- **Additional Scripts**: Various MTG-specific tools in the same directory

### Model Setup
1. **Install Ollama**: Follow Ollama installation instructions
2. **Download Hermes3**: `ollama pull hermes3`
3. **Start Ollama Server**: Ensure Ollama is running locally

## Usage

### Basic Usage
```bash
python mtgLama.py
```

### Interactive Interface
The assistant provides an interactive chat interface with automatic function detection:

```
🤖 Chat Assistant with Function Calling - Type 'quit' or 'exit' to end
📅 Current Time: Monday, January 15, 2024 at 2:30:45 PM
🔧 Available functions: DateTime, Card Price Lookup, Card Image Identification, Web Search, Trend/News Collector, Cost-to-Value Search
🐛 Debug mode: OFF

👤 User: What's the current price of Lightning Bolt?
🔧 The following functions may help answer your question: Card Price Lookup
```

### Function Detection
The assistant automatically detects when functions are needed based on keywords:

- **"card price"** → Card Price Lookup
- **"identify card"** → Card Image Identification  
- **"latest news"** → Web Search
- **"market trends"** → Trend/News Collector
- **"investment analysis"** → Cost-to-Value Search

### Manual Function Selection
Users can manually select functions using the menu system:

```
👤 User: menu
=== Function Menu ===
1. DateTime (keywords: date, time, now, current, today)
2. Card Price Lookup (keywords: card price, mtg price, how much is, value of, price of)
3. Card Image Identification (keywords: card identifier, card image identification, identify card image, what card is this image, card from image)
4. Web Search (keywords: search, find, look up, web search, latest, recent, current, news, update)
5. Trend/News Collector (keywords: news, trend, trending, article, finance, market)
6. Cost-to-Value Search (keywords: cost to value, profit margin, best box set, box set deal, sealed box set, best set to buy, best new set, cost value, value search, investment, roi, cost to value function, cost-to-value, run cost to value, box set profit, mtg box set)
=====================
```

## Function Details

### DateTime Function
Provides comprehensive time information:
```python
{
    "iso_format": "2024-01-15T14:30:45.123456",
    "readable": "Monday, January 15, 2024 at 2:30:45 PM",
    "date": "2024-01-15",
    "time": "14:30:45",
    "components": {
        "year": 2024,
        "month": 1,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "second": 45
    }
}
```

### Card Price Lookup
- **Input**: Card name
- **Output**: Current market price, price history, market trends
- **Sources**: Integrated price databases and APIs
- **Features**: Price alerts, market analysis, historical data

### Card Image Identification
- **Input**: Image file path (JPG, PNG)
- **Output**: Card name, set, collector number, additional details
- **Processing**: Computer vision and OCR analysis
- **Accuracy**: High-precision card recognition

### Web Search
- **Input**: Search query
- **Output**: Current web search results with AI summarization
- **Engine**: Brave search integration
- **Features**: Real-time information, current events, latest updates

### Trend/News Collector
- **Input**: MTG-specific query
- **Output**: Curated news and market analysis
- **Focus**: Magic: The Gathering community and market
- **Features**: Financial analysis, community trends, market insights

### Cost-to-Value Search
- **Input**: Investment analysis request
- **Output**: ROI analysis, market comparisons, investment recommendations
- **Scope**: Sealed products, box sets, individual cards
- **Features**: Profit margin analysis, market timing, investment strategies

## Advanced Features

### Debug Mode
Toggle debug mode for detailed logging:
```
👤 User: debug
🐛 Debug mode: ON
```

### Context Management
- **Conversation History**: Maintains context across interactions
- **Relevant Retrieval**: Searches past conversations for relevance
- **Memory Optimization**: Efficient storage and retrieval
- **Context Awareness**: Uses previous interactions to improve responses

### Error Handling
- **Graceful Degradation**: Continues operation even if functions fail
- **Detailed Error Messages**: Provides specific error information
- **Fallback Mechanisms**: Alternative approaches when primary methods fail
- **Recovery Options**: Suggestions for resolving issues

## Configuration

### Model Settings
```python
# AI Model Configuration
MODEL_NAME = "hermes3"
TEMPERATURE = 0.1  # Low temperature for consistent responses
STREAMING = True   # Real-time response generation
```

### Database Settings
```python
# ChromaDB Configuration
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "mtgchathistory"
MAX_RESULTS = 3    # Number of relevant past conversations to retrieve
```

### Function Registry
```python
# Function Configuration
FUNCTION_REGISTRY = [
    {
        "name": "DateTime",
        "func": get_present_datetime,
        "keywords": ["date", "time", "now", "current", "today"]
    },
    # ... additional functions
]
```

## Integration

### With Other MTG Tools
- **Card Detection**: Integrates with `detectname.py` for image processing
- **Price Databases**: Connects with MTG price tracking systems
- **Inventory Management**: Compatible with card shop inventory systems
- **eBay Listing**: Works with eBay listing automation tools

### External APIs
- **Scryfall API**: Card information and pricing
- **MTG Price APIs**: Market data and trends
- **News APIs**: MTG community news and updates
- **Search APIs**: Web search and information retrieval

## Performance Optimization

### Response Speed
- **Streaming Responses**: Real-time response generation
- **Function Caching**: Caches function results for faster access
- **Parallel Processing**: Concurrent function execution where possible
- **Optimized Queries**: Efficient database queries and searches

### Memory Management
- **History Limiting**: Maintains manageable conversation history
- **Garbage Collection**: Automatic cleanup of old data
- **Efficient Storage**: Optimized data structures for conversation storage
- **Resource Monitoring**: Tracks memory and processing usage

## Troubleshooting

### Common Issues

#### Ollama Connection Errors
```
❌ Error: Could not connect to Ollama server
```
**Solution**: Ensure Ollama is running and accessible

#### Function Import Errors
```
❌ Error: Could not import required function
```
**Solution**: Verify all dependent scripts are in the same directory

#### Database Errors
```
❌ Error: ChromaDB connection failed
```
**Solution**: Check database permissions and disk space

#### Model Loading Issues
```
❌ Error: Could not load AI model
```
**Solution**: Verify model is downloaded and accessible

### Debug Information
Enable debug mode for detailed troubleshooting:
```python
DEBUG_MODE = True
```

## Future Development

### Planned Enhancements

#### 1. Advanced AI Features
- **Multi-Modal AI**: Support for image and text combined processing
- **Voice Interface**: Speech-to-text and text-to-speech capabilities
- **Predictive Analytics**: AI-powered market predictions and trends
- **Personalization**: User-specific preferences and learning

#### 2. Enhanced Functionality
- **Deck Building Assistant**: AI-powered deck construction and optimization
- **Tournament Analysis**: Competitive format analysis and meta insights
- **Collection Management**: Advanced inventory and collection tracking
- **Market Arbitrage**: Cross-platform price comparison and arbitrage opportunities

#### 3. Integration Improvements
- **API Expansion**: More comprehensive API integrations
- **Real-Time Data**: Live market data and price feeds
- **Social Media**: Integration with MTG social media platforms
- **Community Features**: User interaction and community building

#### 4. Performance Optimizations
- **GPU Acceleration**: CUDA support for faster AI processing
- **Distributed Processing**: Multi-server processing capabilities
- **Caching Systems**: Advanced caching for improved response times
- **Load Balancing**: Automatic load distribution across resources

#### 5. User Experience
- **Web Interface**: Browser-based user interface
- **Mobile App**: iOS and Android applications
- **Voice Commands**: Hands-free operation
- **Customizable UI**: User-configurable interface elements

#### 6. Advanced Analytics
- **Market Intelligence**: Comprehensive market analysis tools
- **Investment Tracking**: Portfolio management and performance tracking
- **Trend Prediction**: AI-powered market trend forecasting
- **Risk Assessment**: Investment risk analysis and recommendations

#### 7. Automation Features
- **Scheduled Tasks**: Automated price monitoring and alerts
- **Batch Processing**: Bulk operations for multiple cards
- **Auto-Listing**: Automatic eBay listing based on market conditions
- **Inventory Sync**: Real-time inventory synchronization

#### 8. Community Features
- **User Profiles**: Personalized user accounts and preferences
- **Sharing**: Share analyses and insights with the community
- **Collaboration**: Multi-user collaboration features
- **Marketplace**: Community marketplace for card trading

### Technical Improvements

#### 1. Architecture Enhancements
- **Microservices**: Modular service architecture
- **Containerization**: Docker support for easy deployment
- **Cloud Integration**: AWS, Azure, and Google Cloud support
- **Scalability**: Horizontal and vertical scaling capabilities

#### 2. Data Management
- **Big Data Processing**: Handle large-scale MTG data
- **Real-Time Analytics**: Live data processing and analysis
- **Data Visualization**: Interactive charts and graphs
- **Machine Learning**: Advanced ML models for predictions

#### 3. Security Enhancements
- **Authentication**: User authentication and authorization
- **Data Encryption**: Secure data storage and transmission
- **API Security**: Secure API access and rate limiting
- **Privacy Protection**: GDPR and privacy compliance

## Support

### Getting Help
1. **Check Documentation**: Review this README and function documentation
2. **Enable Debug Mode**: Use debug mode for detailed error information
3. **Verify Setup**: Ensure all dependencies and models are properly installed
4. **Test Functions**: Test individual functions to isolate issues

### Best Practices
1. **Regular Updates**: Keep AI models and dependencies updated
2. **Backup Data**: Regularly backup conversation history and settings
3. **Monitor Performance**: Track system performance and resource usage
4. **User Training**: Provide user training for optimal usage

## License

This tool is designed for Magic: The Gathering card shop automation and AI assistance. 