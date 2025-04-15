import faker
import pandas as pd
import numpy as np

def generate_post_data(num_posts=5000):
    data = pd.DataFrame()
    fake = faker.Faker()
    
    # Define base engagement rates for each post type
    base_rates = {
        'Video': {'likes': 3500, 'comments': 1500, 'shares': 1000, 'views': 4000},
        'Carousel': {'likes': 3000, 'comments': 1200, 'shares': 800, 'views': 3500},
        'Image': {'likes': 2500, 'comments': 1000, 'shares': 600, 'views': 3000},
        'Text': {'likes': 2000, 'comments': 800, 'shares': 400, 'views': 2500}
    }
    
    # Generate posts
    for i in range(num_posts):
        post_type = np.random.choice(['Video', 'Carousel', 'Image', 'Text'])
        base = base_rates[post_type]
        
        # Add some randomness while maintaining relationships
        data.loc[i, 'PostType'] = post_type
        data.loc[i, 'PostID'] = fake.uuid4()
        data.loc[i, 'PostDate'] = fake.date_time_between(start_date='-1y', end_date='now')
        data.loc[i, 'PostContent'] = fake.text()
        
        # Generate engagement metrics with realistic variations
        data.loc[i, 'PostLikes'] = int(base['likes'] * np.random.uniform(0.7, 1.3))
        data.loc[i, 'PostComments'] = int(base['comments'] * np.random.uniform(0.7, 1.3))
        data.loc[i, 'PostShares'] = int(base['shares'] * np.random.uniform(0.7, 1.3))
        data.loc[i, 'PostViews'] = int(base['views'] * np.random.uniform(0.7, 1.3))
    
    return data

# Generate and save data
data = generate_post_data()
data.to_csv('generated_data.csv', index=False)
print("Data generated successfully!")
   