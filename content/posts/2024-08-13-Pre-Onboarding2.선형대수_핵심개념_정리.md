---
image: "/images/posts/2024-08-13-Pre-Onboarding2/cover.jpg"
categories:
- machine-learning
date: '2024-08-13'
math: true
tags:
- machine-learning
- job-interview
title: '[원티드_프리온보딩]2.선형대수 핵심개념 정리'
toc: true
---
## 선형대수 핵심개념 정리

### 행렬 (Matrix)

- **행렬(Matrix):** 수 또는 다항식을 직사각형 배열로 나타낸 것으로, 행과 열로 구성됩니다. 행렬은 데이터의 변환, 시스템의 표현, 기하학적 변환 등을 나타내는 데 사용됩니다.

  - **예시:** 실수 1, 9, -13, 20, 5, -16을 2행 3열의 직사각형 형태로 배열한 행렬.

  $$
  A = \begin{bmatrix}
  1 & 9 & -13 \\
  20 & 5 & -16
  \end{bmatrix}
  $$

  
  
  - 행렬은 다양한 연산이 가능하며, 예를 들어 두 행렬 \( A \)와 \( B \)의 곱셈은 다음과 같이 정의됩니다.
  
  $$
  C = AB = \begin{bmatrix} 
  a_{11} & a_{12} \\ 
  a_{21} & a_{22} 
  \end{bmatrix} 
  \begin{bmatrix} 
  b_{11} & b_{12} \\ 
  b_{21} & b_{22} 
  \end{bmatrix} 
  = \begin{bmatrix} 
  a_{11}b_{11} + a_{12}b_{21} & a_{11}b_{12} + a_{12}b_{22} \\ 
  a_{21}b_{11} + a_{22}b_{21} & a_{21}b_{12} + a_{22}b_{22} 
  \end{bmatrix}
  $$
  
  

### 벡터 (Vector)

- **벡터(Vector):** 크기와 방향을 함께 가지는 물리량으로, 수학적으로는 좌표 공간의 점을 나타냅니다. 벡터는 덧셈, 뺄셈, 내적, 외적 등의 연산이 가능합니다.

  - **벡터의 예시:**

  $$
  \mathbf{v} = \begin{bmatrix} 3 \\ 4 \end{bmatrix}
  $$

  
  
  - **벡터의 내적(Dot Product):** 두 벡터 $ \mathbf{u} = \begin{bmatrix} u_1 \\ u_2 \end{bmatrix} $와 $ \mathbf{v} = \begin{bmatrix} v_1 \\ v_2 \end{bmatrix} $의 내적은 다음과 같이 계산됩니다.
  
  $$
  \mathbf{u} \cdot \mathbf{v} = u_1v_1 + u_2v_2
  $$
  
  

### 생성(Span)과 기저(Basis)

- **생성(Span):** 주어진 벡터 집합의 선형 결합으로 얻을 수 있는 모든 벡터들의 집합입니다.

  - 예를 들어, 벡터 $ \mathbf{a} $와 $ \mathbf{b} $가 주어졌을 때, 이 벡터들의 span은 모든 선형 결합 $ c_1\mathbf{a} + c_2\mathbf{b} $으로 표현됩니다.

- **기저(Basis):** 벡터 공간에서 모든 벡터를 유일하게 표현할 수 있는 최소한의 벡터 집합으로, 서로 선형 독립인 벡터들로 구성됩니다.

### 선형 독립 (Linearly Independent)

- **선형 독립(Linearly Independent):** 벡터 집합에서 임의의 벡터를 다른 벡터의 선형 결합으로 표현할 수 없는 경우를 의미합니다. 즉, 벡터들이 서로 독립적으로 존재합니다.

  - 벡터 $ \mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3 $가 선형 독립이라면 다음 식이 성립합니다:

  $$
  c_1\mathbf{v}_1 + c_2\mathbf{v}_2 + c_3\mathbf{v}_3 = \mathbf{0} \implies c_1 = c_2 = c_3 = 0
  $$

  

### 행렬식 (Determinant) 및 고유값과 고유벡터

- **행렬식(Determinant):** 정방행렬의 스칼라 값으로, 행렬의 가역성을 판별하는 데 사용됩니다. 행렬식이 0이 아니면 행렬은 가역이며, $ \det(A) $로 표현됩니다.

  - 예를 들어, 2x2 행렬의 행렬식은 다음과 같이 계산됩니다:

  $$
  \det(A) = \begin{vmatrix} a & b \\ c & d \end{vmatrix} = ad - bc
  $$

  

- **고유값(Eigenvalue)과 고유벡터(Eigenvector):** 행렬의 선형 변환에서 벡터가 같은 방향으로 유지되면서 크기만 변할 때 그 벡터를 고유벡터, 변하는 크기를 고유값이라고 합니다.

  - 고유값 방정식: $ A\mathbf{v} = \lambda\mathbf{v} $, 여기서 $ \lambda $는 고유값이고 $ \mathbf{v} $는 고유벡터입니다.

### 계수 (Rank)

- **계수(Rank):** 행렬의 선형적으로 독립인 행 또는 열의 최대 개수로, $ \text{Rank}(A) $로 표현됩니다. 계수는 연립방정식의 해의 존재성과 유일성을 판단하는 데 사용됩니다.

### 차원의 저주 (The Curse of Dimensionality)

- **차원의 저주:** 데이터의 차원이 증가함에 따라 데이터가 희소(Sparse)해지고, 모델의 성능이 저하되는 현상입니다. 차원이 커지면 데이터 포인트 간의 거리 차이가 극단적으로 커지면서 데이터 분석과 머신러닝 모델의 성능에 악영향을 미칠 수 있습니다.

### 차원 축소 (Dimensional Reduction)

- **차원 축소:** 고차원 데이터를 저차원 데이터로 변환하여 데이터의 중요 정보를 보존하면서 데이터의 복잡성을 줄이는 기법입니다.

  - **Feature Selection (특성 선택):** 통계적 방법을 사용해 중요한 특징을 선택하는 방법으로, 상관분석, 전/후진선택 등이 있습니다.

  - **Feature Extraction (특성 추출):** 기존 특징을 사용하여 새로운 유용한 특징을 생성하는 방법으로, PCA, LDA 등이 있습니다.

### PCA와 LDA

- **PCA(Principal Component Analysis, 주성분 분석):** 변수 간 상관관계를 이용해 주성분을 추출하여 차원을 축소하는 기법으로, 가장 큰 분산을 가지는 축을 기반으로 차원을 축소합니다.

  - 데이터의 분산을 최대화하는 새로운 축을 정의하여 차원을 축소합니다. 

  - 예시: 2차원 데이터를 1차원으로 투영

- **LDA(Linear Discriminant Analysis, 선형판별분석):** 클래스 간 분산을 최대화하고 클래스 내 분산을 최소화하는 고유값과 고유벡터를 찾아 선형 변환하는 방법입니다.

  - LDA는 데이터의 분리 가능성을 최대화하는 새로운 축을 찾습니다.

  - 예시: 2차원 데이터에서 클래스 간 분리를 최대화하는 방향으로 투영

