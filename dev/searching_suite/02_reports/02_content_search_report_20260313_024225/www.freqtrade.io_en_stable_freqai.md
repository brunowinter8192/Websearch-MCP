# Introduction - Freqtrade
**URL:** https://www.freqtrade.io/en/stable/freqai/
**Domain:** www.freqtrade.io
**Score:** 72.0
**Source:** scraped
**Query:** freqai freqtrade machine learning trading bot

---

# FreqAI[¶](https://www.freqtrade.io/en/stable/freqai/#freqai "Permanent link")
## Introduction[¶](https://www.freqtrade.io/en/stable/freqai/#introduction "Permanent link")
FreqAI is a software designed to automate a variety of tasks associated with training a predictive machine learning model to generate market forecasts given a set of input signals. In general, FreqAI aims to be a sandbox for easily deploying robust machine learning libraries on real-time data ([details](https://www.freqtrade.io/en/stable/freqai/#freqai-position-in-open-source-machine-learning-landscape)).
Note
FreqAI is, and always will be, a not-for-profit, open source project. FreqAI does _not_ have a crypto token, FreqAI does _not_ sell signals, and FreqAI does not have a domain besides the present [freqtrade documentation](https://www.freqtrade.io/en/stable/freqai/).
Features include:
  * **Self-adaptive retraining** - Retrain models during [live deployments](https://www.freqtrade.io/en/stable/freqai-running/#live-deployments) to self-adapt to the market in a supervised manner
  * **Rapid feature engineering** - Create large rich [feature sets](https://www.freqtrade.io/en/stable/freqai-feature-engineering/#feature-engineering) (10k+ features) based on simple user-created strategies
  * **High performance** - Threading allows for adaptive model retraining on a separate thread (or on GPU if available) from model inferencing (prediction) and bot trade operations. Newest models and data are kept in RAM for rapid inferencing
  * **Realistic backtesting** - Emulate self-adaptive training on historic data with a [backtesting module](https://www.freqtrade.io/en/stable/freqai-running/#backtesting) that automates retraining
  * **Extensibility** - The generalized and robust architecture allows for incorporating any [machine learning library/method](https://www.freqtrade.io/en/stable/freqai-configuration/#using-different-prediction-models) available in Python. Eight examples are currently available, including classifiers, regressors, and a convolutional neural network
  * **Smart outlier removal** - Remove outliers from training and prediction data sets using a variety of [outlier detection techniques](https://www.freqtrade.io/en/stable/freqai-feature-engineering/#outlier-detection)
  * **Crash resilience** - Store trained models to disk to make reloading from a crash fast and easy, and [purge obsolete files](https://www.freqtrade.io/en/stable/freqai-running/#purging-old-model-data) for sustained dry/live runs
  * **Automatic data normalization** - [Normalize the data](https://www.freqtrade.io/en/stable/freqai-feature-engineering/#building-the-data-pipeline) in a smart and statistically safe way
  * **Automatic data download** - Compute timeranges for data downloads and update historic data (in live deployments)
  * **Cleaning of incoming data** - Handle NaNs safely before training and model inferencing
  * **Dimensionality reduction** - Reduce the size of the training data via [Principal Component Analysis](https://www.freqtrade.io/en/stable/freqai-feature-engineering/#data-dimensionality-reduction-with-principal-component-analysis)
  * **Deploying bot fleets** - Set one bot to train models while a fleet of [consumers](https://www.freqtrade.io/en/stable/producer-consumer/) use signals.


## Quick start[¶](https://www.freqtrade.io/en/stable/freqai/#quick-start "Permanent link")
The easiest way to quickly test FreqAI is to run it in dry mode with the following command:
```
freqtradetrade--configconfig_examples/config_freqai.example.json--strategyFreqaiExampleStrategy--freqaimodelLightGBMRegressor--strategy-pathfreqtrade/templates

```

[Content truncated...]