# Long-Term Degradation Diagnosis

The engine integrates the 365-day trend, Vital Score history, recurrence, seasonality,
and recovery evidence.

## Safety gates

- strong seasonality prevents a chronic-degradation diagnosis
- current recovery prevents a degradation diagnosis
- LOW_SAMPLE reduces confidence
- fewer than six windows returns insufficient history

## Outcomes

- Chronic Degradation
- Sharp Degradation
- CTR Degradation
- Position Degradation
- Seasonal Variation
- Recovery in Progress
- Insufficient History
