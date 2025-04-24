import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import csv

# Initialize Faker
fake = Faker()

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Constants
POST_TYPES = ['reel', 'image', 'carousel', 'video']
# Times with higher engagement probability
PEAK_HOURS = [
    (8, 10),  # Morning
    (12, 14), # Lunch break
    (19, 22)  # Evening
]
# Days with higher engagement probability
PEAK_DAYS = ['Saturday', 'Sunday', 'Friday']

# Generate mock data
def generate_mock_data(num_records=5000):
    data = []
    
    # Generate timestamps spread over the last year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    timestamps = [fake.date_time_between(start_date=start_date, end_date=end_date) for _ in range(num_records)]
    
    for timestamp in timestamps:
        post_type = random.choice(POST_TYPES)
        
        # Base engagement metrics
        base_likes = random.randint(10, 1000)
        
        # Adjust metrics based on post type
        if post_type == 'reel':
            likes = int(base_likes * random.uniform(1.5, 3.0))
            comments = int(likes * random.uniform(0.05, 0.2))
            shares = int(likes * random.uniform(0.1, 0.3))
            views = int(likes * random.uniform(10, 30))
        elif post_type == 'image':
            likes = int(base_likes * random.uniform(0.7, 1.5))
            comments = int(likes * random.uniform(0.03, 0.1))
            shares = int(likes * random.uniform(0.05, 0.15))
            views = int(likes * random.uniform(3, 10))
        elif post_type == 'carousel':
            likes = int(base_likes * random.uniform(1.0, 2.0))
            comments = int(likes * random.uniform(0.04, 0.15))
            shares = int(likes * random.uniform(0.08, 0.2))
            views = int(likes * random.uniform(5, 15))
        else:  # video
            likes = int(base_likes * random.uniform(1.2, 2.5))
            comments = int(likes * random.uniform(0.04, 0.18))
            shares = int(likes * random.uniform(0.08, 0.25))
            views = int(likes * random.uniform(8, 25))
        
        # Adjust for time of day
        hour = timestamp.hour
        is_peak_hour = any(start <= hour <= end for start, end in PEAK_HOURS)
        if is_peak_hour:
            likes = int(likes * random.uniform(1.2, 1.5))
            comments = int(comments * random.uniform(1.2, 1.5))
            shares = int(shares * random.uniform(1.2, 1.5))
            views = int(views * random.uniform(1.2, 1.5))
        
        # Adjust for day of week
        day_name = timestamp.strftime('%A')
        if day_name in PEAK_DAYS:
            likes = int(likes * random.uniform(1.1, 1.3))
            comments = int(comments * random.uniform(1.1, 1.3))
            shares = int(shares * random.uniform(1.1, 1.3))
            views = int(views * random.uniform(1.1, 1.3))
        
        # Generate caption with random text
        caption_length = random.randint(1, 5)
        caption = " ".join(fake.sentences(caption_length))
        
        # Generate hashtags (0-5)
        hashtag_count = random.randint(0, 5)
        hashtags = " ".join([f"#{fake.word()}" for _ in range(hashtag_count)])
        
        # Combine caption and hashtags
        content = f"{caption} {hashtags}".strip()
        
        data.append({
            'post_id': fake.uuid4(),
            'post_type': post_type,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'likes': likes,
            'comments': comments,
            'shares': shares,
            'views': views,
            'content': content,
            'day_of_week': day_name,
            'hour': hour
        })
    
    return pd.DataFrame(data)

# Generate and save data
def main():
    print("Generating 5000 records of mock social media engagement data...")
    df = generate_mock_data(5000)
    
    # Save to CSV
    output_file = 'social_media_engagement_data.csv'
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"Data successfully saved to {output_file}")
    
    # Print sample
    print("\nSample data (first 5 rows):")
    print(df.head())
    
    # Print summary statistics
    print("\nSummary statistics by post type:")
    print(df.groupby('post_type')[['likes', 'comments', 'shares', 'views']].mean())

if __name__ == "__main__":
    main()