from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from social_media_rag import SocialMediaEngagementRAG  # Import our RAG class
from fastapi import Request, Response

# Initialize the FastAPI app
app = FastAPI(
    title="Social Media Analytics RAG API",
    description="API for social media engagement analytics using RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://social-media-engagement-analytics-rag.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Length"],
    max_age=3600,
)

# Initialize the RAG system - lazy loading
rag_system = None

# Simple in-memory chat history store
chat_histories = {}

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class ChatMessage(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str

class AnalyticsRequest(BaseModel):
    post_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metric: Optional[str] = None

class AnalyticsResponse(BaseModel):
    data: Dict[str, Any]
    chart_url: Optional[str] = None

# Mock auth dependency
async def get_current_user():
    """Mock auth dependency - disabled for testing"""
    return "test_user-123"

# Helper function to initialize RAG system on demand
def get_rag_system():
    global rag_system
    if rag_system is None:
        try:
            rag_system = SocialMediaEngagementRAG()
            rag_system.load()
        except Exception as e:
            print(f"Error initializing RAG system: {e}")
            raise
    return rag_system

# Routes
@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api/ping")
async def ping():
    return {"pong": True}

@app.options("/api/chat", include_in_schema=False)
async def options_chat(request: Request):
    headers = {
        "Access-Control-Allow-Origin": request.headers.get("origin") or "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Allow-Credentials": "true",
    }
    return Response(status_code=200, headers=headers)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, user_id: str = Depends(get_current_user)):
    """Process a chat message and return a response from the RAG system"""
    try:
        # Get RAG system
        rag = get_rag_system()
        
        # Get existing chat history or create new one
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        
        # Add message to history and limit size
        chat_histories[user_id].append({"role": "user", "content": message.message})
        # Keep only last 20 messages for context window
        if len(chat_histories[user_id]) > 20:
            chat_histories[user_id] = chat_histories[user_id][-20:]
        
        # Format chat history for our RAG system
        formatted_history = [(msg["content"], None) if msg["role"] == "user" else (None, msg["content"]) 
                             for msg in chat_histories[user_id][:-1]]
        
        # Get response from RAG system
        response = rag.query(message.message, formatted_history)
        
        # Add response to history
        chat_histories[user_id].append({"role": "assistant", "content": response})
        
        return ChatResponse(response=response)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )

@app.get("/api/chat/history")
async def get_chat_history(user_id: str = Depends(get_current_user)):
    """Get the chat history for a user"""
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    
    return {"history": chat_histories[user_id]}

# Mock analytics data
MOCK_ANALYTICS = {
    "reel": {
        "engagement_rate": 4.2,
        "avg_likes": 420,
        "avg_comments": 32,
        "avg_shares": 57,
        "best_time": "19:00",
        "best_day": "Sunday",
        "total_posts": 120
    },
    "image": {
        "engagement_rate": 1.9,
        "avg_likes": 210,
        "avg_comments": 18,
        "avg_shares": 12,
        "best_time": "12:00",
        "best_day": "Wednesday",
        "total_posts": 350
    },
    "carousel": {
        "engagement_rate": 3.1,
        "avg_likes": 315,
        "avg_comments": 28,
        "avg_shares": 25,
        "best_time": "20:00",
        "best_day": "Saturday",
        "total_posts": 210
    },
    "video": {
        "engagement_rate": 2.8,
        "avg_likes": 280,
        "avg_comments": 24,
        "avg_shares": 35,
        "best_time": "21:00",
        "best_day": "Friday",
        "total_posts": 90
    }
}

@app.post("/api/analytics", response_model=AnalyticsResponse)
async def get_analytics(request: AnalyticsRequest, user_id: str = Depends(get_current_user)):
    """Get analytics data based on the requested parameters"""
    if request.post_type and request.post_type in MOCK_ANALYTICS:
        data = MOCK_ANALYTICS[request.post_type]
    else:
        # Summary across all post types
        data = {
            "engagement_rate_by_type": {
                "reel": 4.2,
                "image": 1.9,
                "carousel": 3.1,
                "video": 2.8
            },
            "best_times": {
                "reel": "19:00",
                "image": "12:00",
                "carousel": "20:00",
                "video": "21:00"
            },
            "best_days": {
                "reel": "Sunday",
                "image": "Wednesday",
                "carousel": "Saturday",
                "video": "Friday"
            },
            "post_distribution": {
                "reel": 120,
                "image": 350,
                "carousel": 210,
                "video": 90
            }
        }
    
    # Generate a chart
    chart_type = "engagement_by_post_type"
    if request.post_type:
        chart_type = f"performance_{request.post_type}"
    
    chart_url = f"/mock-charts/{chart_type}.png"
    
    return AnalyticsResponse(data=data, chart_url=chart_url)

# Recommendation data
RECOMMENDATIONS = {
    "general": [
        "Post at least 3-4 times per week to maintain audience engagement",
        "Use 3-5 relevant hashtags per post to increase discoverability",
        "Include a clear call-to-action in your captions to boost comment rates",
        "Respond to comments within 1 hour to increase follower loyalty",
        "Analyze your top-performing posts monthly and create similar content"
    ],
    "reel": [
        "Keep reels under 30 seconds for highest completion rates",
        "Use trending audio to increase discoverability",
        "Include text overlays for viewers watching without sound",
        "Start with a strong hook in the first 3 seconds",
        "Post reels on Sunday evening between 6-8 PM for maximum reach"
    ],
    "image": [
        "Use high-quality, bright images that stand out in the feed",
        "Ask a question in the caption to encourage comments",
        "Consider converting some image posts to carousels for higher engagement",
        "Post images mid-week during lunch hours (11 AM - 1 PM)",
        "Include a human element in your images when possible"
    ],
    "carousel": [
        "Use 3-10 slides for optimal engagement",
        "Put your strongest image first to encourage swipes",
        "Include a mix of informational and visual slides",
        "Add a CTA on the final slide",
        "Use carousels for tutorials and multi-part stories"
    ],
    "video": [
        "Keep videos under 2 minutes for highest completion rates",
        "Add captions to increase accessibility",
        "Include a custom thumbnail that entices clicks",
        "Post videos in the evening (7-9 PM) when viewers have more time",
        "Structure videos with a clear beginning, middle and end"
    ]
}

@app.get("/api/recommendations")
@app.get("/recommendations")
async def get_recommendations(post_type: Optional[str] = None, user_id: str = Depends(get_current_user)):
    """Get AI-powered recommendations for improving engagement"""
    if post_type and post_type in RECOMMENDATIONS:
        return {"recommendations": RECOMMENDATIONS[post_type]}
    else:
        return {"recommendations": RECOMMENDATIONS["general"]}

# Best times data
BEST_TIMES = {
    "reel": {"day": "Sunday", "time": "19:00", "reason": "31% higher engagement than average"},
    "image": {"day": "Wednesday", "time": "12:00", "reason": "22% higher engagement than average"},
    "carousel": {"day": "Saturday", "time": "20:00", "reason": "27% higher engagement than average"},
    "video": {"day": "Friday", "time": "21:00", "reason": "25% higher engagement than average"}
}

@app.get("/api/best-times")
@app.get("/best-times")
async def get_best_times(post_type: Optional[str] = None, user_id: str = Depends(get_current_user)):
    """Get recommended best times to post based on historical engagement"""
    if post_type and post_type in BEST_TIMES:
        return {"best_time": BEST_TIMES[post_type]}
    else:
        return {"best_times": BEST_TIMES}

# Metrics summary data
METRICS_SUMMARY = {
    "total_posts": 770,
    "total_likes": 247500,
    "total_comments": 21840,
    "total_shares": 28950,
    "total_views": 9250000,
    "avg_engagement_rate": 3.2,
    "best_post_type": "reel",
    "best_time_overall": "19:00 Sunday"
}

@app.get("/api/metrics/summary")
@app.get("/metrics/summary")
async def get_metrics_summary(user_id: str = Depends(get_current_user)):
    """Get a summary of key metrics across all post types"""
    return METRICS_SUMMARY

@app.post("/api/upload")
@app.post("/upload")
async def upload_data(user_id: str = Depends(get_current_user)):
    """Endpoint for uploading new social media data (mock)"""
    return {"status": "success", "message": "Data uploaded and processed successfully"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

# Run with: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    # Use the PORT environment variable that Render provides
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)