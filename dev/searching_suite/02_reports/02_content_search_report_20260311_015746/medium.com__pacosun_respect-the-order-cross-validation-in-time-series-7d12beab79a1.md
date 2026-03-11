# Time Series Cross-Validation: Best Practices - Medium
**URL:** https://medium.com/@pacosun/respect-the-order-cross-validation-in-time-series-7d12beab79a1
**Domain:** medium.com
**Score:** 8.0
**Source:** scraped
**Query:** walk-forward validation time series cross-validation trading

---

[Sitemap](https://medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
# Cross-Validation in Time Series
Follow
8 min read May 4, 2025
Share
Press enter or click to view image in full size
If you’re using regular k-fold cross-validation on your time series data, you’re essentially cheating on your test scores. It’s like peeking at tomorrow’s stock prices to predict today’s, sounds great until you deploy your model and watch it collapse in real-world conditions.
The issue is standard k-fold treats your data like a well-shuffled deck of cards, assuming each observation is **independent and identically distributed (IID)**.
But time series data doesn’t play by those rules. When your target variable at 3 PM is influenced by what happened at 2:59 PM, that shuffle-and-split approach becomes about as useful as a weather forecast based on randomly ordered historical data.
The problem runs deeper than just chronological order. Time series often contain **autocorrelations, seasonal patterns, trends, and other temporal dependencies** that make neighbouring observations anything but independent. So when you randomly shuffle your data before splitting it into folds, you’re accidentally allowing your model to peek into the future.
The good news is that there are methods that preserve the arrow of time, ensuring your models are tested on truly unseen future data.
In this article, we’ll cover:
  * Rolling origin and time-aware validation methods
  * Avoiding temporal data leakage
  * Handling seasonality and special events
  * Choosing the right strategy for your time series


## Why Standard Cross-Validation Fails in Time Series?
Let’s see why standard k-fold is a temporal timed bomb. Here’s a simple example using daily stock prices:
```
import pandas as pdimport numpy as npfrom sklearn.model_selection import KFold# Create sample time series datadates = pd.date_range(start='2024-01-01', end='2024-01-20', freq='D')np.random.seed(42)prices = 100 + np.cumsum(np.random.randn(20) * 0.5)  # Random walkdf = pd.DataFrame({'date': dates, 'price': prices})print("Dataset preview:")print(df.head())
```

Output:
```
Dataset preview:        date      price0 2024-01-01  100.2483571 2024-01-02  100.1792252 2024-01-03  100.5030693 2024-01-04  101.2645844 2024-01-05  101.147507
```

Now let’s apply standard K-Fold:
```
# Apply naive K-Foldkf = KFold(n_splits=3, shuffle=True, random_state=101)for fold, (train_idx, test_idx) in enumerate(kf.split(df)):    print(f"\nFold {fold+1}:")    print(f"Train dates: {df.iloc[train_idx]['date'].dt.strftime('%Y-%m-%d').tolist()[:5]}...")    print(f"Test dates: {df.iloc[test_idx]['date'].dt.strftime('%Y-%m-%d').tolist()}")
```

Output:
```
Fold 1:Train dates: ['2024-01-01', '2024-01-05', '2024-01-06', '2024-01-07',              '2024-01-09']...Test dates:  ['2024-01-02', '2024-01-03', '2024-01-04', '2024-01-08',              '2024-01-11', '2024-01-15', '2024-01-17']Fold 2:Train dates: ['2024-01-02', '2024-01-03', '2024-01-04', '2024-01-07',              '2024-01-08']...Test dates:  ['2024-01-01', '2024-01-05', '2024-01-06', '2024-01-09',              '2024-01-13', '2024-01-14', '2024-01-19']Fold 3:Train dates: ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04',              '2024-01-05']...Test dates:  ['2024-01-07', '2024-01-10', '2024-01-12', '2024-01-16',              '2024-01-18', '2024-01-20']
```

[Content truncated...]