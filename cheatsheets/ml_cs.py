"""
Machine Learning Cheatsheet (Python / Scikit-Learn)
===================================================
Prerequisites:
pip install numpy pandas scikit-learn matplotlib seaborn torch xgboost

Sections:
1. Data Preprocessing
2. Regression Algorithms
3. Classification Algorithms
4. Clustering Algorithms
5. Dimensionality Reduction
6. Model Evaluation
7. Deep Learning Basics (PyTorch)
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# ==============================================================================
# 1. DATA PREPROCESSING
# ==============================================================================

def preprocess_data(df, target_col):
    """
    Standard preprocessing pipeline.
    USE CASE: Preparing raw data for ML models. Most models cannot handle missing values or strings.
    """
    X = df.drop(target_col, axis=1)
    y = df[target_col]
    
    # Split Data
    # Stratify is useful for classification to maintain class balance
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Identify columns
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
    categorical_features = X.select_dtypes(include=['object']).columns
    
    # Transformers
    # Imputation: Filling missing values (Median is robust to outliers)
    # Scaling: Standardization (Mean=0, Std=1) is crucial for distance-based algos (KNN, SVM, LR)
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # OneHotEncoder: Converts categories to binary columns (e.g., Color_Red, Color_Blue)
    # handle_unknown='ignore': Crucial for production to handle new categories seen in test data
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
        
    return X_train, X_test, y_train, y_test, preprocessor

# ==============================================================================
# 2. REGRESSION ALGORITHMS (Predict Continuous Value)
# ==============================================================================

from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
import xgboost as xgb

def regression_examples(X_train, y_train):
    # 1. Linear Regression
    # USE CASE: Baseline model, determining feature importance (coefficients).
    # EXAMPLE: Predicting house price based on square footage.
    # PROS: Fast, interpretable. CONS: Assumes linear relationship, sensitive to outliers.
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    
    # 2. Ridge Regression (L2 Regularization)
    # USE CASE: When you have multicollinearity (correlated features).
    # EXAMPLE: Predicting GDP where many economic indicators are correlated.
    # NOTE: Shrinks coefficients towards zero but not exactly zero.
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    
    # 3. Lasso Regression (L1 Regularization)
    # USE CASE: Feature selection.
    # EXAMPLE: Genetics data with thousands of genes (features) but only a few matter.
    # NOTE: Can shrink coefficients to exactly zero, effectively removing features.
    lasso = Lasso(alpha=0.1)
    lasso.fit(X_train, y_train)
    
    # 4. Random Forest Regressor
    # USE CASE: Complex non-linear relationships, robust to outliers.
    # EXAMPLE: Predicting customer lifetime value based on diverse behavioral data.
    # PROS: Handles non-linearities, no scaling needed. CONS: Slow prediction, large model size.
    rf = RandomForestRegressor(n_estimators=100, max_depth=10)
    rf.fit(X_train, y_train)
    
    # 5. XGBoost Regressor (Gradient Boosting)
    # USE CASE: High-performance competitions, structured/tabular data.
    # EXAMPLE: Predicting ride-hailing demand or insurance claims.
    # PROS: State-of-the-art performance, handles missing values. CONS: Many hyperparameters to tune.
    xg_reg = xgb.XGBRegressor(objective ='reg:squarederror', n_estimators=100)
    xg_reg.fit(X_train, y_train)

# ==============================================================================
# 3. CLASSIFICATION ALGORITHMS (Predict Category)
# ==============================================================================

from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB

def classification_examples(X_train, y_train):
    # 1. Logistic Regression
    # USE CASE: Binary classification, need probabilities.
    # EXAMPLE: Will a user click an ad? (Yes/No)
    # PROS: Interpretable (odds ratio), fast. CONS: Linear decision boundary.
    log_reg = LogisticRegression()
    log_reg.fit(X_train, y_train)
    
    # 2. K-Nearest Neighbors (KNN)
    # USE CASE: Small datasets, spatial data, simple recommendation baselines.
    # EXAMPLE: Recommending products based on "users like you".
    # PROS: Simple, no training phase. CONS: Slow prediction (lazy learner), sensitive to scale.
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X_train, y_train)
    
    # 3. Support Vector Machine (SVM)
    # USE CASE: High-dimensional data, clear margin separation.
    # EXAMPLE: Text classification, image classification (with few pixels).
    # PROS: Effective in high dimensions. CONS: Slow on large datasets, hard to tune C/Gamma.
    svm = SVC(kernel='rbf', C=1.0, probability=True)
    svm.fit(X_train, y_train)
    
    # 4. Decision Tree
    # USE CASE: Need white-box model, explainable rules.
    # EXAMPLE: Loan approval (If Income > X and Credit Score > Y then Approve).
    # PROS: Easy to visualize. CONS: Prone to overfitting (memorizing data).
    dt = DecisionTreeClassifier(max_depth=5)
    dt.fit(X_train, y_train)
    
    # 5. Random Forest
    # USE CASE: General purpose "workhorse", reduces variance of Decision Trees.
    # EXAMPLE: Fraud detection, churn prediction.
    # PROS: Very accurate, handles high dimensions. CONS: Less interpretable than single tree.
    rf_clf = RandomForestClassifier(n_estimators=100)
    rf_clf.fit(X_train, y_train)
    
    # 6. Naive Bayes
    # USE CASE: Text classification, NLP.
    # EXAMPLE: Spam filtering (Spam vs Ham), Sentiment Analysis.
    # PROS: Very fast, works well with high-dimensional sparse data (text). CONS: Assumes feature independence.
    nb = GaussianNB()
    nb.fit(X_train, y_train)

# ==============================================================================
# 4. CLUSTERING ALGORITHMS (Unsupervised)
# ==============================================================================

from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering

def clustering_examples(X):
    # 1. K-Means
    # USE CASE: General purpose clustering, customer segmentation.
    # EXAMPLE: Grouping customers by purchasing behavior (High spenders, Frequent buyers).
    # PROS: Fast, scalable. CONS: Must specify K, assumes spherical clusters, sensitive to outliers.
    kmeans = KMeans(n_clusters=3, random_state=42)
    labels = kmeans.fit_predict(X)
    
    # 2. DBSCAN (Density-Based Spatial Clustering)
    # USE CASE: Spatial data, finding outliers/noise, clusters of arbitrary shapes.
    # EXAMPLE: Clustering GPS locations to find hotspots, anomaly detection in network traffic.
    # PROS: No need to specify K, handles noise. CONS: Hard to tune epsilon/min_samples.
    dbscan = DBSCAN(eps=0.5, min_samples=5)
    labels_db = dbscan.fit_predict(X)
    
    # 3. Hierarchical Clustering (Agglomerative)
    # USE CASE: When you need a hierarchy/taxonomy of clusters.
    # EXAMPLE: Biological taxonomy (grouping species), document organization.
    # PROS: Visualizable (Dendrogram). CONS: Computationally expensive O(N^3) or O(N^2).
    agg = AgglomerativeClustering(n_clusters=3)
    labels_agg = agg.fit_predict(X)

# ==============================================================================
# 5. DIMENSIONALITY REDUCTION
# ==============================================================================

from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

def dim_reduction_examples(X):
    # 1. PCA (Principal Component Analysis)
    # USE CASE: Visualization, noise reduction, pre-processing to speed up training.
    # EXAMPLE: Reducing 100 image features to 10 principal components.
    # NOTE: Linear transformation. Preserves global structure (variance).
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)
    print(f"Explained Variance Ratio: {pca.explained_variance_ratio_}")
    
    # 2. t-SNE (t-Distributed Stochastic Neighbor Embedding)
    # USE CASE: Visualization of high-dimensional data (2D or 3D plots).
    # EXAMPLE: Visualizing word embeddings (Word2Vec) or MNIST digits.
    # NOTE: Non-linear. Preserves local structure (neighbors). Computationally heavy.
    tsne = TSNE(n_components=2, perplexity=30)
    X_tsne = tsne.fit_transform(X)

# ==============================================================================
# 6. MODEL EVALUATION
# ==============================================================================

from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             confusion_matrix, classification_report, roc_auc_score,
                             mean_squared_error, r2_score)

def evaluate_model(model, X_test, y_test, task='classification'):
    y_pred = model.predict(X_test)
    
    if task == 'classification':
        # Accuracy: Overall correctness. Bad for imbalanced data.
        print("Accuracy:", accuracy_score(y_test, y_pred))
        
        # Classification Report: Precision, Recall, F1-Score per class.
        # Precision: Exactness (TP / (TP + FP)) - Minimize False Positives (e.g., Spam filter).
        # Recall: Sensitivity (TP / (TP + FN)) - Minimize False Negatives (e.g., Cancer detection).
        print("Classification Report:\n", classification_report(y_test, y_pred))
        
        # Confusion Matrix: Raw counts of TP, TN, FP, FN.
        print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
        
        # ROC-AUC: Ability to distinguish between classes. 0.5 = Random, 1.0 = Perfect.
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test)[:, 1]
            print("ROC AUC:", roc_auc_score(y_test, y_prob))
            
    elif task == 'regression':
        # RMSE: Root Mean Squared Error. Penalizes large errors. Same unit as target.
        print("RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))
        # R2 Score: Goodness of fit. 1.0 = Perfect, 0.0 = Baseline (mean).
        print("R2 Score:", r2_score(y_test, y_pred))

# ==============================================================================
# 7. DEEP LEARNING BASICS (PyTorch)
# ==============================================================================

import torch
import torch.nn as nn
import torch.optim as optim

class SimpleNN(nn.Module):
    """
    Simple Feed-Forward Neural Network.
    USE CASE: Complex non-linear patterns, unstructured data (images, audio).
    """
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU() # Activation function (introduces non-linearity)
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid() # Output activation for binary classification (0-1)
        
    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        out = self.sigmoid(out)
        return out

def train_torch_model(X_train, y_train):
    # Convert numpy arrays to PyTorch tensors
    X_tensor = torch.FloatTensor(X_train)
    y_tensor = torch.FloatTensor(y_train).view(-1, 1)
    
    # Initialize Model, Loss, Optimizer
    model = SimpleNN(input_dim=X_train.shape[1], hidden_dim=10, output_dim=1)
    criterion = nn.BCELoss() # Binary Cross Entropy Loss (Standard for binary classification)
    optimizer = optim.Adam(model.parameters(), lr=0.01) # Adam is a good default optimizer
    
    # Training Loop
    for epoch in range(100):
        # 1. Forward pass
        outputs = model(X_tensor)
        loss = criterion(outputs, y_tensor)
        
        # 2. Backward pass and optimization
        optimizer.zero_grad() # Clear gradients
        loss.backward()       # Compute gradients
        optimizer.step()      # Update weights
        
        if (epoch+1) % 10 == 0:
            print(f'Epoch [{epoch+1}/100], Loss: {loss.item():.4f}')

if __name__ == "__main__":
    print("This is a cheatsheet. Import functions or copy code snippets as needed.")
