# Feature Engineering for Time-Series Data: A Deep Yet Intuitive Guide.
**URL:** https://medium.com/@karanbhutani477/feature-engineering-for-time-series-data-a-deep-yet-intuitive-guide-b544aeb26ec2
**Domain:** medium.com
**Score:** 16.0
**Source:** scraped
**Query:** feature engineering financial time series prediction

---

[Sitemap](https://medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
Press enter or click to view image in full size
# Feature Engineering for Time-Series Data: A Deep Yet Intuitive Guide.
Follow
5 min read Feb 7, 2025
Share
## How to Transform Raw Time-Series Data into Powerful Predictions
## 1. Introduction: The Unique Challenges of Time-Series Data
Time-series forecasting is a cornerstone of decision-making in fields like **finance, energy management, and weather prediction**. Yet, applying machine learning models to time-series data is not straightforward. Unlike traditional datasets, where observations are independent, time-series data is inherently **sequential** — past events influence future outcomes.
Most machine learning models, including decision trees and gradient boosting algorithms like **XGBoost** , treat data as a static table. They excel at recognizing patterns in structured datasets but **lack an inherent understanding of time**. If past values of a stock price or electricity demand are not explicitly incorporated, the model has no way of learning temporal relationships.
This is where **feature engineering** becomes essential. It allows us to transform raw time-series data into a form that machine learning models can process effectively. In this guide, we will focus on three core techniques:
  1. **Lag Features** — Explicitly incorporating past values to provide context.
  2. **Rolling Window Features** — Capturing trends and volatility over time.
  3. **Sine-Cosine Encoding** — Properly representing cyclical time-based features.


Each method will be explored in-depth, emphasizing its impact on model performance, with real-world analogies drawn from finance, energy, and signal processing to illustrate these concepts.
## 2. Lag Features: Giving the Model a Memory
## Why Do We Need Lag Features?
Consider the problem of **predicting electricity demand** for a city. The demand at any given time is highly influenced by recent values — what happened in the last hour, the last day, or even the same day last week.
Yet, if we simply provide a dataset with columns for “temperature,” “humidity,” and “hour of the day,” the model will have no way of knowing whether demand is **increasing, decreasing, or following a weekly pattern**. It sees only the present moment, not the past.
To address this, we introduce **lag features** — columns that store past values of the target variable.
## How to Implement Lag Features in Python.
```
import pandas as pd# Creating Lag Featuresdf["lag_1"] = df["value"].shift(1)   # Yesterday's valuedf["lag_7"] = df["value"].shift(7)   # Value from a week agodf["lag_30"] = df["value"].shift(30) # Value from 30 days agodf.dropna(inplace=True)  # Remove NaNs caused by shifting
```

## How Lag Features Improve Model Predictions
Tree-based models like XGBoost **split data into decision nodes** based on observed relationships. By adding lag features:
  * The model **learns that recent values are predictive** — if power demand was high yesterday, it may remain high today.
  * If there is **a weekly trend** , the model recognizes that the value from 7 days ago is an important predictor.
  * If a time series exhibits **monthly seasonality** , the 30-day lag provides critical context.


[Content truncated...]