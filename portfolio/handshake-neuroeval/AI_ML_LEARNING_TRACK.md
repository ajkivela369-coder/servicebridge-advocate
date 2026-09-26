# AI/ML Learning Track

NeuroEval is now the main learning surface for AJ's AI/ML portfolio work.

## Stage 1 — Classical NLP + Machine Learning

Implemented in this branch:

1. **TF-IDF vectorization**
   - converts text into numeric features;
   - exposes unigram and bigram features;
   - provides an inspectable baseline before neural embeddings.

2. **Logistic-regression text classification**
   - learns PASS / REVIEW / FAIL labels from labeled examples;
   - uses class balancing and deterministic random state;
   - demonstrates supervised learning without pretending the tiny dataset is production-ready.

3. **Stratified cross-validation**
   - keeps class proportions represented across folds;
   - measures predictions on examples excluded from each training fold;
   - produces accuracy, precision, recall, F1, and a confusion matrix.

4. **TF-IDF retrieval baseline**
   - converts a query and benchmark answers into the same feature space;
   - ranks examples with cosine similarity;
   - creates a baseline to compare against future embedding retrieval for Elias.

## Concepts AJ should be able to explain

### NLP
Text must be represented numerically before a classical ML model can use it. TF-IDF gives more
weight to terms that are useful in a document while reducing the influence of terms that appear
everywhere.

### Supervised machine learning
The classifier receives examples where the correct label is already known. It learns feature
weights that help separate PASS, REVIEW, and FAIL.

### Train/evaluation separation
A model should not be judged only on the same examples it learned from. Cross-validation
repeatedly trains on part of the dataset and evaluates on held-out examples.

### Precision vs recall
Precision asks: "When the model predicted this class, how often was it right?"
Recall asks: "Of the real examples in this class, how many did the model find?"

### Confusion matrix
Rows and columns show which labels the classifier confuses. This is often more useful than one
accuracy number.

## Limits

The current NeuroEval benchmark is intentionally small. Metrics are learning artifacts, not
claims about general model performance. The next step is to expand the synthetic/public benchmark
before drawing meaningful conclusions.

## Stage 2 — Embeddings

Next we will compare the TF-IDF retrieval baseline with sentence embeddings on the same retrieval
questions. If embedding retrieval materially improves relevant-source recall without unacceptable
false matches, that result can inform an optional Elias retrieval upgrade.

## Stage 3 — Deep learning

After the classical baseline is understood, add a small PyTorch text classifier and document:
tensors, layers, activation functions, loss, gradient descent, backpropagation, epochs, validation,
and overfitting. We will compare it against logistic regression rather than assuming a neural
network is better.
