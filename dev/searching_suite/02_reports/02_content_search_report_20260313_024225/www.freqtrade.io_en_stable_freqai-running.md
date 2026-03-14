# Running FreqAI - Freqtrade
**URL:** https://www.freqtrade.io/en/stable/freqai-running/
**Domain:** www.freqtrade.io
**Score:** 28.0
**Source:** scraped
**Query:** freqai freqtrade machine learning trading bot

---

# Running FreqAI[¶](https://www.freqtrade.io/en/stable/freqai-running/#running-freqai "Permanent link")
There are two ways to train and deploy an adaptive machine learning model - live deployment and historical backtesting. In both cases, FreqAI runs/simulates periodic retraining of models as shown in the following figure:
## Live deployments[¶](https://www.freqtrade.io/en/stable/freqai-running/#live-deployments "Permanent link")
FreqAI can be run dry/live using the following command:
```
freqtradetrade--strategyFreqaiExampleStrategy--configconfig_freqai.example.json--freqaimodelLightGBMRegressor

```

When launched, FreqAI will start training a new model, with a new `identifier`, based on the config settings. Following training, the model will be used to make predictions on incoming candles until a new model is available. New models are typically generated as often as possible, with FreqAI managing an internal queue of the coin pairs to try to keep all models equally up to date. FreqAI will always use the most recently trained model to make predictions on incoming live data. If you do not want FreqAI to retrain new models as often as possible, you can set `live_retrain_hours` to tell FreqAI to wait at least that number of hours before training a new model. Additionally, you can set `expired_hours` to tell FreqAI to avoid making predictions on models that are older than that number of hours.
Trained models are by default saved to disk to allow for reuse during backtesting or after a crash. You can opt to [purge old models](https://www.freqtrade.io/en/stable/freqai-running/#purging-old-model-data) to save disk space by setting `"purge_old_models": true` in the config.
To start a dry/live run from a saved backtest model (or from a previously crashed dry/live session), you only need to specify the `identifier` of the specific model:
```
"freqai":{
"identifier":"example",
"live_retrain_hours":0.5
}

```

In this case, although FreqAI will initiate with a pre-trained model, it will still check to see how much time has elapsed since the model was trained. If a full `live_retrain_hours` has elapsed since the end of the loaded model, FreqAI will start training a new model.
### Automatic data download[¶](https://www.freqtrade.io/en/stable/freqai-running/#automatic-data-download "Permanent link")
FreqAI automatically downloads the proper amount of data needed to ensure training of a model through the defined `train_period_days` and `startup_candle_count` (see the [parameter table](https://www.freqtrade.io/en/stable/freqai-parameter-table/) for detailed descriptions of these parameters). 
### Saving prediction data[¶](https://www.freqtrade.io/en/stable/freqai-running/#saving-prediction-data "Permanent link")
All predictions made during the lifetime of a specific `identifier` model are stored in `historic_predictions.pkl` to allow for reloading after a crash or changes made to the config.
### Purging old model data[¶](https://www.freqtrade.io/en/stable/freqai-running/#purging-old-model-data "Permanent link")
FreqAI stores new model files after each successful training. These files become obsolete as new models are generated to adapt to new market conditions. If you are planning to leave FreqAI running for extended periods of time with high frequency retraining, you should enable `purge_old_models` in the config:
```
"freqai":{
"purge_old_models":4,
}

```

This will automatically purge all models older than the four most recently trained ones to save disk space. Inputing "0" will never purge any models.
## Backtesting[¶](https://www.freqtrade.io/en/stable/freqai-running/#backtesting "Permanent link")
The FreqAI backtesting module can be executed with the following command:
```
freqtradebacktesting--strategyFreqaiExampleStrategy--strategy-pathfreqtrade/templates--configconfig_examples/config_freqai.example.json--freqaimodelLightGBMRegressor--timerange20210501-20210701

```

[Content truncated...]