import os
import pandas as pd
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any

from datetime import datetime
import json

# Set environment variables for API keys (you should set these in your environment)
os.environ["GROQ_API_KEY"] = "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"  # Replace with your actual key

class SocialMediaEngagementRAG:
    def __init__(self, data_path="social_media_engagement_data.csv"):
        self.data_path = data_path
        self.embeddings = None
        self.llm = None
        self.vector_store = None
        self.stats = None
        self.prompt = None
        self._loaded = False
        self.df = None

    def load(self):
        if self._loaded:
            return
        
        # Load embeddings and LLM lazily
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.llm = ChatGroq(model="llama3-8b-8192")  # Use a smaller model for memory
        self.prompt = PromptTemplate.from_template(
            """You are a helpful social media analytics assistant. Based on the following context, 
            answer the user's question. If the user is just greeting you (saying hi, hello, etc.), 
            respond with a simple greeting back.

            Context: {context}
            Question: {question}
            
            Answer: """
        )
        
        # Load stats from JSON if available
        stats_path = "stats.json"
        self.stats = None
        if os.path.exists(stats_path):
            try:
                with open(stats_path, "r") as f:
                    self.stats = json.load(f)
            except json.JSONDecodeError:
                print("Error loading stats.json, will regenerate")
                self.stats = None
        
        # Load FAISS index if present
        index_path = "faiss_index"
        if os.path.exists(index_path):
            try:
                self.vector_store = FAISS.load_local(index_path, self.embeddings)
            except Exception as e:
                print(f"Error loading FAISS index: {e}, will regenerate")
                self.vector_store = None
        
        # If vector_store is None or stats is None, regenerate from CSV
        if self.vector_store is None or self.stats is None:
            if not os.path.exists(self.data_path):
                raise RuntimeError("Stats not found and data file missing. Cannot initialize analytics.")
            
            self.df = pd.read_csv(self.data_path)
            if self.stats is None:
                self._generate_statistical_summaries(self.df)
            
            if self.vector_store is None:
                documents = self._create_documents(self.df)
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
                self.vector_store.save_local(index_path)
        
        self._loaded = True

    def _unload(self):
        """Unload resources to save memory"""
        if self.df is not None:
            del self.df
            self.df = None

    def _generate_statistical_summaries(self, df):
        """Generate statistical summaries to be included in the vector store"""
        # Convert NumPy types to native Python types
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.int8, np.int16, np.int32, np.int64,
                               np.uint8, np.uint16, np.uint32, np.uint64)):
                return int(obj)
            elif isinstance(obj, (np.float16, np.float32, np.float64)):
                return float(obj)
            return obj

        # Common statistics across all data
        self.stats = {
            "total_posts": int(len(df)),
            "post_type_distribution": convert_numpy_types(df['post_type'].value_counts().to_dict()),
            "avg_engagement_by_type": convert_numpy_types(df.groupby('post_type')[['likes', 'comments', 'shares', 'views']].mean().to_dict()),
            "best_time_by_post_type": {},
            "best_day_by_post_type": {},
            "engagement_rate_by_type": {}
        }
        
        # Calculate engagement rate (likes + comments + shares) / views
        df['engagement_rate'] = (df['likes'] + df['comments'] + df['shares']) / df['views']
        
        # Find best posting times by post type
        for post_type in df['post_type'].unique():
            post_type_df = df[df['post_type'] == post_type]
            
            # Best hour analysis
            hour_engagement = post_type_df.groupby('hour')['engagement_rate'].mean().sort_values(ascending=False)
            if not hour_engagement.empty:
                self.stats["best_time_by_post_type"][post_type] = int(hour_engagement.index[0])
            else:
                self.stats["best_time_by_post_type"][post_type] = 12  # Default to noon if no data
            
            # Best day analysis
            day_engagement = post_type_df.groupby('day_of_week')['engagement_rate'].mean().sort_values(ascending=False)
            if not day_engagement.empty:
                self.stats["best_day_by_post_type"][post_type] = str(day_engagement.index[0])
            else:
                self.stats["best_day_by_post_type"][post_type] = "Monday"  # Default to Monday if no data
            
            # Overall engagement rate
            self.stats["engagement_rate_by_type"][post_type] = float(post_type_df['engagement_rate'].mean())
        
        # Save stats to JSON for reuse
        with open("stats.json", "w") as f:
            json.dump(self.stats, f)

    def _create_documents(self, df) -> List[Document]:
        """Convert dataframe rows and statistics into LangChain documents"""
        documents = []
        
        # Add overall statistics document
        stat_doc = Document(
            page_content=f"""
            SOCIAL MEDIA ANALYTICS SUMMARY
            ============================
            
            POST TYPE PERFORMANCE METRICS:
            
            REEL POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['reel']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['reel']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['reel']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['reel']:.1f}
            
            IMAGE POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['image']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['image']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['image']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['image']:.1f}
            
            VIDEO POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['video']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['video']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['video']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['video']:.1f}
            
            CAROUSEL POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['carousel']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['carousel']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['carousel']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['carousel']:.1f}
            
            OTHER STATISTICS:
            - Total posts analyzed: {self.stats['total_posts']}
            - Post type distribution: {json.dumps(self.stats['post_type_distribution'])}
            """,
            metadata={
                "document_type": "statistics",
                "source": "aggregated_data"
            }
        )
        documents.append(stat_doc)
        
        # Add detailed post type analysis documents
        for post_type in df['post_type'].unique():
            pt_df = df[df['post_type'] == post_type]
            
            # Time analysis
            hour_engagement = pt_df.groupby('hour')['engagement_rate'].mean().sort_values(ascending=False)
            top_hours = hour_engagement.head(3).index.tolist() if not hour_engagement.empty else [12, 18, 9]
            
            # Day analysis
            day_engagement = pt_df.groupby('day_of_week')['engagement_rate'].mean().sort_values(ascending=False)
            top_days = day_engagement.head(3).index.tolist() if not day_engagement.empty else ["Monday", "Thursday", "Saturday"]
            
            doc = Document(
                page_content=f"""
                Detailed analysis for {post_type} posts:
                Average likes: {pt_df['likes'].mean():.1f}
                Average comments: {pt_df['comments'].mean():.1f}
                Average shares: {pt_df['shares'].mean():.1f}
                Average views: {pt_df['views'].mean():.1f}
                Engagement rate: {pt_df['engagement_rate'].mean():.3f}
                Best posting hours: {top_hours}
                Best posting days: {top_days}
                Post count: {len(pt_df)}
                Performance compared to other types: {self._get_comparative_rank(df, post_type)}
                """,
                metadata={
                    "document_type": "post_type_analysis",
                    "post_type": post_type
                }
            )
            documents.append(doc)
        
        # Add hour and day of week analysis
        hour_doc = Document(
            page_content=f"""
            Hour of day engagement analysis:
            {self._format_hour_analysis(df)}
            """,
            metadata={"document_type": "time_analysis"}
        )
        documents.append(hour_doc)
        
        day_doc = Document(
            page_content=f"""
            Day of week engagement analysis:
            {self._format_day_analysis(df)}
            """,
            metadata={"document_type": "day_analysis"}
        )
        documents.append(day_doc)
        
        # Add "improvement recommendations" documents specific to each post type
        for post_type in df['post_type'].unique():
            doc = Document(
                page_content=self._get_improvement_recommendations(df, post_type),
                metadata={
                    "document_type": "recommendations",
                    "post_type": post_type
                }
            )
            documents.append(doc)
        
        # Add sample post data (every 100th post to avoid too many documents)
        for i, row in df.iloc[::100].iterrows():
            doc = Document(
                page_content=f"""
                Sample {row['post_type']} post:
                Posted: {row['timestamp']} ({row['day_of_week']} at hour {row['hour']})
                Content: {row['content']}
                Performance: {row['likes']} likes, {row['comments']} comments, {row['shares']} shares, {row['views']} views
                Engagement rate: {(row['likes'] + row['comments'] + row['shares']) / row['views']:.3f}
                """,
                metadata={
                    "document_type": "sample_post",
                    "post_type": row['post_type'],
                    "post_id": row['post_id'],
                    "day": row['day_of_week'],
                    "hour": row['hour']
                }
            )
            documents.append(doc)
        
        return documents
    
    def _get_comparative_rank(self, df, post_type):
        """Generate comparative analysis text for a given post type"""
        # Get average metrics for this post type
        metrics = self.stats['avg_engagement_by_type']
        current_type_metrics = {
            'likes': metrics['likes'][post_type],
            'comments': metrics['comments'][post_type],
            'shares': metrics['shares'][post_type],
            'views': metrics['views'][post_type]
        }
        
        # Compare with other post types
        comparison = []
        for metric in ['likes', 'comments', 'shares', 'views']:
            metric_values = {pt: metrics[metric][pt] for pt in metrics['likes'].keys()}
            sorted_types = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
            rank = next((i+1 for i, (pt, _) in enumerate(sorted_types) if pt == post_type), len(sorted_types))
            total = len(sorted_types)
            comparison.append(f"{metric}: {rank} of {total}")
        
        # Build detailed comparison text
        result = f"Performance metrics for {post_type} posts:\n"
        result += f"- Average likes: {current_type_metrics['likes']:.1f}\n"
        result += f"- Average comments: {current_type_metrics['comments']:.1f}\n"
        result += f"- Average shares: {current_type_metrics['shares']:.1f}\n"
        result += f"- Average views: {current_type_metrics['views']:.1f}\n\n"
        result += "Ranking by metric:\n"
        result += "\n".join(f"- {c}" for c in comparison)
        
        return result
    
    def _format_hour_analysis(self, df):
        """Format hour-by-hour engagement analysis"""
        hour_engagement = df.groupby('hour')['engagement_rate'].mean().sort_values(ascending=False)
        top_hours = hour_engagement.head(5).index.tolist() if not hour_engagement.empty else [12, 18, 9, 19, 20]
        bottom_hours = hour_engagement.tail(5).index.tolist() if not hour_engagement.empty else [3, 4, 5, 2, 1]
        
        result = f"Peak engagement hours: {top_hours}\n"
        result += f"Lowest engagement hours: {bottom_hours}\n\n"
        
        # Add type-specific best hours
        result += "Best hours by post type:\n"
        for post_type in df['post_type'].unique():
            best_hour = self.stats["best_time_by_post_type"][post_type]
            result += f"- {post_type}: {best_hour}:00\n"
        
        return result
    
    def _format_day_analysis(self, df):
        """Format day-by-day engagement analysis"""
        day_engagement = df.groupby('day_of_week')['engagement_rate'].mean().sort_values(ascending=False)
        
        result = "Day of week engagement ranking (best to worst):\n"
        if not day_engagement.empty:
            for i, (day, rate) in enumerate(day_engagement.items(), 1):
                result += f"{i}. {day}: {rate:.3f} engagement rate\n"
        else:
            result += "(No day-specific engagement data available)\n"
        
        result += "\nBest days by post type:\n"
        for post_type in df['post_type'].unique():
            best_day = self.stats["best_day_by_post_type"][post_type]
            result += f"- {post_type}: {best_day}\n"
        
        return result
    
    def _get_improvement_recommendations(self, df, post_type):
        """Generate improvement recommendations for a specific post type"""
        pt_df = df[df['post_type'] == post_type]
        best_hour = self.stats["best_time_by_post_type"][post_type]
        best_day = self.stats["best_day_by_post_type"][post_type]
        
        # Find high-performing content patterns
        high_engagement_count = max(1, int(len(pt_df) * 0.1))  # Ensure at least 1 row
        high_engagement = pt_df.nlargest(high_engagement_count, 'engagement_rate')
        
        avg_hashtags = 0
        avg_text_length = 0
        
        if not high_engagement.empty:
            avg_hashtags = high_engagement['content'].apply(lambda x: x.count('#') if isinstance(x, str) else 0).mean()
            avg_text_length = high_engagement['content'].apply(lambda x: len(x) if isinstance(x, str) else 0).mean()
        
        recommendations = f"""
        Improvement recommendations for {post_type} posts:
        
        1. Posting Strategy:
           - Best time to post: {best_hour}:00
           - Best day to post: {best_day}
           - Consider creating a posting schedule that targets these peak engagement times
        
        2. Content Strategy:
           - Optimal hashtag count: {avg_hashtags:.1f} hashtags
           - Optimal content length: {avg_text_length:.0f} characters
        
        3. Engagement Tactics:
        """
        
        # Add type-specific recommendations
        if post_type == 'reel':
            recommendations += """
           - Keep videos short (15-30 seconds) to maximize retention
           - Use trending audio or music to increase discoverability
           - Include a strong hook in the first 3 seconds
           - Add text overlays for viewers watching without sound
        """
        elif post_type == 'image':
            recommendations += """
           - Use high-quality, visually striking images
           - Incorporate strong color contrast to stand out in feeds
           - Ask a question in the caption to encourage comments
           - Consider carousel posts which typically outperform single images
        """
        elif post_type == 'carousel':
            recommendations += """
           - Put your strongest image first to encourage swipes
           - Use 3-10 slides for optimal engagement
           - Tell a coherent story across slides
           - Include a call-to-action in the final slide
        """
        elif post_type == 'video':
            recommendations += """
           - Focus on the first 10 seconds to capture attention
           - Add captions to increase accessibility and engagement
           - Keep videos under 2 minutes for highest completion rates
           - End with a clear call-to-action
        """
        
        return recommendations
    
    def create_qa_chain(self):
        """Create a QA chain for answering questions about the engagement data"""
        # Create a prompt template for answering questions
        template = """
        You are a Social Media Analytics Expert specializing in post engagement analysis.
        
        Here is the current social media performance data:
        {context}
        
        Previous conversation:
        {chat_history}
        
        Based on the above data, answer this question: {input}
        
        IMPORTANT GUIDELINES:
        1. ONLY use metrics shown in the data above. DO NOT make up or hallucinate data.
        2. For post type comparisons:
           - ALWAYS compare ALL metrics (likes, comments, shares, views, engagement rate)
           - Present metrics in a properly formatted markdown table with aligned columns
           - Use the exact table format shown in the example below
           - Highlight which type performs better in each metric
           - Format numbers with appropriate precision (1 decimal for engagement metrics, 2 decimals for percentages)
           - Provide a clear overall recommendation
        3. If asked about timing, hashtags, or other data not shown above, state that this information is not available.
        4. Keep responses factual and data-driven, avoiding speculation.
        5. If the data shows something different from what you might expect, trust the data.
        
        Example comparison format:
        When comparing different post types:
        
        | Metric          | Reel Posts | Image Posts | Video Posts | Carousel Posts | Better Performer |
        |-----------------|------------|-------------|-------------|----------------|------------------|
        | Likes           | X          | X           | X           | X              | [Type]           |
        | Comments        | X          | X           | X           | X              | [Type]           |
        | Shares          | X          | X           | X           | X              | [Type]           |
        | Views           | X          | X           | X           | X              | [Type]           |
        | Engagement Rate | X%         | X%          | X%          | X%             | [Type]           |
        
        Overall recommendation: [Clear statement based on the data]
        
        Format your response in a clear, structured way using markdown.
        """
        
        # Create a simple chain that uses the provided context
        return ChatPromptTemplate.from_template(template) | self.llm
    
    def query(self, query: str, chat_history: List[tuple] = None) -> str:
        try:
            self.load()
            # Check for greetings
            query_lower = query.lower()
            greetings = ['hi', 'hello', 'hey', 'greetings']
            if any(greeting == query_lower.strip() for greeting in greetings):
                return "Hello! How can I help you analyze your social media engagement today?"

            # Fail gracefully if stats is missing
            if self.stats is None:
                return "Sorry, analytics data is currently unavailable. Please try again later or contact support."
            
            # Create the QA chain if not already created
            chain = self.create_qa_chain()
            
            # Format chat history
            formatted_history = []
            if chat_history:
                for human, ai in chat_history:
                    if human is not None:
                        formatted_history.extend([f"Human: {human}"])
                    if ai is not None:
                        formatted_history.extend([f"Assistant: {ai}"])
            
            # Calculate engagement rates as percentages for display
            engagement_rates = {}
            for post_type, rate in self.stats['engagement_rate_by_type'].items():
                engagement_rates[post_type] = f"{rate:.2%}"
            
            # Format statistics directly
            stats_content = f"""
            SOCIAL MEDIA ANALYTICS SUMMARY
            ============================
            
            POST TYPE PERFORMANCE METRICS:
            
            REEL POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['reel']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['reel']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['reel']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['reel']:.1f}
            - Best posting time: {self.stats['best_time_by_post_type']['reel']:02d}:00 hours
            - Best posting day: {self.stats['best_day_by_post_type']['reel']}
            - Average engagement rate: {engagement_rates['reel']}
            
            IMAGE POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['image']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['image']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['image']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['image']:.1f}
            - Best posting time: {self.stats['best_time_by_post_type']['image']:02d}:00 hours
            - Best posting day: {self.stats['best_day_by_post_type']['image']}
            - Average engagement rate: {engagement_rates['image']}
            
            VIDEO POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['video']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['video']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['video']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['video']:.1f}
            - Best posting time: {self.stats['best_time_by_post_type']['video']:02d}:00 hours
            - Best posting day: {self.stats['best_day_by_post_type']['video']}
            - Average engagement rate: {engagement_rates['video']}
            
            CAROUSEL POSTS:
            - Average likes: {self.stats['avg_engagement_by_type']['likes']['carousel']:.1f}
            - Average comments: {self.stats['avg_engagement_by_type']['comments']['carousel']:.1f}
            - Average shares: {self.stats['avg_engagement_by_type']['shares']['carousel']:.1f}
            - Average views: {self.stats['avg_engagement_by_type']['views']['carousel']:.1f}
            - Best posting time: {self.stats['best_time_by_post_type']['carousel']:02d}:00 hours
            - Best posting day: {self.stats['best_day_by_post_type']['carousel']}
            - Average engagement rate: {engagement_rates['carousel']}
            
            OTHER STATISTICS:
            - Total posts analyzed: {self.stats['total_posts']}
            - Post type distribution: {json.dumps(self.stats['post_type_distribution'])}
            """
            
            # Get response from chain
            result = chain.invoke({
                "input": query,
                "context": stats_content,
                "chat_history": "\n".join(formatted_history) if formatted_history else ""
            })
            
            if not result or not hasattr(result, 'content'):
                raise ValueError("Invalid response from LLM chain")
            
            return result.content

        except Exception as e:
            import traceback
            print(f"Error in query method: {str(e)}")
            print(traceback.format_exc())
            return f"An error occurred while processing your request: {str(e)}"

        finally:
            try:
                self._unload()
            except Exception as e:
                print(f"Error during unload: {str(e)}")
    
    def generate_charts(self, chart_type="engagement_by_post_type"):
        """Generate visualization charts for various analytics"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Load data if not already loaded
            if self.df is None:
                self.df = pd.read_csv(self.data_path)
            
            # Set styling
            plt.style.use('ggplot')
            
            if chart_type == "engagement_by_post_type":
                # Create a comparison chart of engagement metrics by post type
                fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                fig.suptitle('Engagement Metrics by Post Type', fontsize=16)
                
                metrics = ['likes', 'comments', 'shares', 'views']
                for i, metric in enumerate(metrics):
                    row, col = i // 2, i % 2
                    ax = axes[row, col]
                    
                    data = [self.stats['avg_engagement_by_type'][metric][pt] for pt in ['image', 'video', 'reel', 'carousel']]
                    ax.bar(['Image', 'Video', 'Reel', 'Carousel'], data, color=sns.color_palette("husl", 4))
                    ax.set_title(f'Average {metric.capitalize()}')
                    ax.set_ylabel(metric.capitalize())
                    
                    # Add values on top of bars
                    for j, v in enumerate(data):
                        ax.text(j, v + 0.1, f"{v:.1f}", ha='center')
                
                plt.tight_layout(rect=[0, 0, 1, 0.95])
                plt.savefig('engagement_by_post_type.png')
                return 'engagement_by_post_type.png'
                
            elif chart_type == "best_times":
                # Create a heatmap of engagement by hour and day
                pivot = self.df.pivot_table(
                    index='day_of_week', 
                    columns='hour', 
                    values='engagement_rate', 
                    aggfunc='mean'
                )
                
                # Define day order
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                pivot = pivot.reindex(days)
                
                plt.figure(figsize=(14, 8))
                sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".3f", linewidths=.5)
                plt.title('Engagement Rate by Day and Hour', fontsize=16)
                plt.xlabel('Hour of Day')
                plt.ylabel('Day of Week')
                plt.tight_layout()
                plt.savefig('best_posting_times.png')
                return 'best_posting_times.png'
                
            elif chart_type == "post_type_distribution":
                # Create a pie chart of post type distribution
                counts = self.stats['post_type_distribution']
                labels = list(counts.keys())
                sizes = list(counts.values())
                
                plt.figure(figsize=(10, 8))
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("husl", len(labels)))
                plt.axis('equal')
                plt.title('Distribution of Post Types', fontsize=16)
                plt.tight_layout()
                plt.savefig('post_type_distribution.png')
                return 'post_type_distribution.png'
                
            elif chart_type == "engagement_rate_comparison":
                # Create a bar chart comparing engagement rates
                plt.figure(figsize=(10, 6))
                rates = [self.stats['engagement_rate_by_type'][pt] for pt in ['image', 'video', 'reel', 'carousel']]
                plt.bar(['Image', 'Video', 'Reel', 'Carousel'], rates, color=sns.color_palette("husl", 4))
                plt.title('Engagement Rate by Post Type', fontsize=16)
                plt.ylabel('Engagement Rate')
        finally:
            print("Charts Generated")   # Add percentage values on top of