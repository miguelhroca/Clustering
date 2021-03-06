# -*- coding: utf-8 -*-
"""P2_Clustering.ipynb


## Descripción del problema
La hipótesis de partida es que es posible agrupar de manera automática señales de tráfico a partir de las imágenes de las mismas.

### El conjunto de datos
Para esta práctica usaremos un conjunto de datos recopilado de [Kaggle](https://www.kaggle.com/valentynsichkar/traffic-signs-preprocessed).

El conjunto de datos está formado por un único fichero en formato [pickle](https://docs.python.org/3/library/pickle.html). Cada fila del archivo corresponde a una imagen en color de una señal, por lo que realmente se divide en el valor de cada píxel de la imagen en cada uno de los tres canales RGB.


## Desarrollo de la práctica

Esta práctica ha sido desarrollada por:

* Miguel Hernández Roca
* Mohammed Makhfi Boulaich
"""

# Librerías utilizadas en el análisis y desarrollo de la práctica
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.cluster import SpectralClustering 
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.metrics import silhouette_score as sc
from sklearn.model_selection import GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

"""### Loading Data
La carga del conjunto de datos se realiza mediante la URL del mismo:
"""

# Loading data from an external URL
datos = joblib.load(urlopen("https://drive.upm.es/index.php/s/FtPb5PANs3kgjqj/download"))

"""### Dataset Exploration

Es muy importante poder acceder a los datos de forma cómoda. Para ello, separamos el dataset en distintas variables con nombres que se corresponden con la fuente de información.
"""

# Transform data to be able to plot them easily
x_train = datos['x_train']
y_train = datos['y_train']
x_test = datos['x_test']
y_test = datos['y_test']
x_validation = datos['x_validation']
y_validation = datos['y_validation']
labels = datos['labels']

x_train = x_train.reshape(x_train.shape[0], x_train.shape[1], x_train.shape[2], x_train.shape[3]).transpose(0, 2, 3, 1)
x_test = x_test.reshape(x_test.shape[0], x_test.shape[1], x_test.shape[2], x_test.shape[3]).transpose(0, 2, 3, 1)
x_validation = x_validation.reshape(x_validation.shape[0], x_validation.shape[1], x_validation.shape[2], x_validation.shape[3]).transpose(0, 2, 3, 1)

"""Escalamos los valores a números entre 0 y 1. Y dibujamos una muestra del dataset."""

# Scale values [0..1]
x_train -= x_train.min()
x_train /= x_train.max()

# Plot image
plt.imshow(x_train[4291], cmap='brg')

"""La siguiente función nos permite dibujar muetras aleatorias del dataset:"""

def print_random_images(images, labels, number_of_images_to_display, color_map='hsv'):
   if number_of_images_to_display % 4 == 0:
       num_rows = number_of_images_to_display / 4
   else:
       num_rows = int(number_of_images_to_display / 4) + 1
   random_indices = [np.random.randint(0, images.shape[0]) for n in range(number_of_images_to_display)]
   # print(random_indices)
   for counter in range(number_of_images_to_display):
       index = random_indices[counter]
       plt.subplot(num_rows, 4, counter + 1)
       # plt.axis('off')
       plt.imshow(images[index], cmap=color_map)
       plt.title('Class :{0}, Class Count: {1} '.format(labels[index], list(labels).count(labels[index])))  # np.count_nonzero(labels == labels[index])))
       plt.show()
       print('Image Dimensions: {0}, Min Pixel: {1}, Max Pixel: {2}'.format(images[index].shape, images[index].min(),images[index].max()))
       plt.subplots_adjust(wspace=1)

# Muestras del dataset
print_random_images(x_train, y_train, 10, color_map='brg')

"""### Dimensionality Reduction

La reducción de la dimensionalidad es una técnica de preprocesado para modelos de aprendizaje supervisados. Consiste en reducir el número de variables en una colección de datos.

Las razones por las que nos interesa reducir la dimensionalidad son varias:

*   Porque interesa identificar y eliminar las variables irrelevantes.
*   Porque no siempre el mejor modelo es el que más variables tiene en cuenta.
*   Porque se mejora el rendimiento computacional, lo que se traduce en un ahorro en coste y tiempo.
*   Porque se reduce la complejidad, lo que lleva a facilitar la comprensión del modelo y sus resultados.

Pero antes, necesitamos modificar el dataset de tal manera que obtengamos una matriz bidimensional.
"""

def flatten_data(data):
  df = pd.DataFrame([])
  size = data.shape[0]
  print(size)
  for index in range(0, size):
    row = pd.Series(data[index].flatten())
    df = df.append(row, ignore_index=True)
  return df

x_train = x_train[0:1000] # Muestra
y_train = y_train[0:1000] # Muestra
x_train_df = flatten_data(x_train)

# Now we've got a dataframe
type(x_train_df)

"""#### Principal Component Analysis

El análisis de componentes principales es la técnica más usada para la reducción de la dimensionalidad. Transforma un conjunto de variables correlacionadas en un conjunto menor de variables no correlacionadas, denominadas componentes principales.
"""

# Visualize
pca = PCA()
pca.fit_transform(x_train_df)
pca_variance = pca.explained_variance_

plt.figure(figsize=(8, 6))
plt.bar(range(1000), pca_variance, alpha=0.5, align='center', label='individual variance')
plt.legend()
plt.ylabel('Variance ratio')
plt.xlabel('Principal components')
plt.show()

"""Parece ser que el **17 o 18 de las variables explican el 95% de los resultados**. Por lo tanto, aplicamos el PCA de nuevo, esta vez quedándonos con 25 componentes, 7 más por si acaso, y las mostramos en un gráfico de dispersión para observar su clasificación."""

pca2 = PCA(n_components=25)
pca2.fit(x_train_df)
x_3d = pca2.transform(x_train_df)

plt.figure(figsize=(8,6))
plt.scatter(x_3d[:,0], x_3d[:,5], c=y_train )
plt.show()

# Let's convert the features into the 25 top features. We'll then plot a scatter
# plot of the data point classification based on these 25 features:

"""### Applying clustering techniques

Hasta ahora, todo lo que hemos hecho se puede considerar exploración y transformación del dataset. A continuación, aplicaremos técnicas de clustering que consiste en realizar **agrupaciones** de una serie de vectores de acuerdo con un determinado criterio.
"""

seed = 1337

"""La siguiente función determina qué parametros dan el mejor resultado."""

def cv_silhouette_scorer(estimator, X):
    estimator.fit(X)
    cluster_labels = estimator.labels_
    if len(np.unique(cluster_labels) < 2) :
      return -1.0
    return sc(X, cluster_labels)

"""#### Agglomerative clustering"""

param_dict = {'affinity':['euclidean','manhattan','cosine'],
               'linkage':['complete','average','single']}
cv = [(slice(None), slice(None))]
gs = GridSearchCV(estimator=AgglomerativeClustering(), param_grid=param_dict,
                  scoring=cv_silhouette_scorer, cv=cv, n_jobs=1)
gs.fit(x_3d)

gs.best_params_

agglo = AgglomerativeClustering(n_clusters=10, affinity='euclidean', linkage='complete')
agglo_fit = agglo.fit_predict(x_3d)
print('Silhouette: ', silhouette_score(x_3d, agglo_fit))
print('Rand Index (con ground truth): ', adjusted_rand_score(y_train,agglo_fit))
print('homogeinety completnes', metrics.homogeneity_completeness_v_measure(y_train,agglo_fit))

import matplotlib.pyplot as plt
fig= plt.figure(figsize=(15,15))
plt.scatter(x_3d[:,0],x_3d[:,1],c=agglo_fit)
plt.show()

"""#### Spectral clustering

Esta función genera un **error** reportado en GitHub que, a día de hoy, sigue sin haberse resuelto.
"""

param_dict = {'affinity':['rbf','laplacian','sigmoid','polynomial','linear'],
              'assign_labels':['kmeans', 'discretize']}
cv = [(slice(None), slice(None))]
gs = GridSearchCV(estimator=SpectralClustering(), param_grid=param_dict, 
                  scoring=cv_silhouette_scorer, cv=cv, n_jobs=1)
gs.fit(x_3d)

gs.best_params_

spectral_silhouettes = []
for n_clusters in range(2, 43):
  spectral = SpectralClustering(n_clusters=n_clusters, random_state=seed, affinity='laplacian')
  labels = spectral.fit_predict(x_3d)
  silhouette = silhouette_score(x_3d, labels)
  spectral_silhouettes.append(silhouette)
plt.scatter(range(2,43), spectral_silhouettes) 
plt.show

max_y = max(spectral_silhouettes[4:])  # Find the maximum y value
max_x = spectral_silhouettes.index(max_y)  # Find the x value corresponding to the maximum y value
print(max_x, max_y)

spectral = SpectralClustering(n_clusters=27, random_state=seed, affinity='laplacian')
spectral_fit = spectral.fit_predict(x_3d)
print('Silhouette: ', silhouette_score(x_3d, spectral_fit))
print('Rand Index (con ground truth): ', adjusted_rand_score(y_train,spectral_fit))
print('homogeinety completnes', metrics.homogeneity_completeness_v_measure(y_train,spectral_fit))

import matplotlib.pyplot as plt
fig= plt.figure(figsize=(15,15))
plt.scatter(x_3d[:,0],x_3d[:,1],c=spectral_fit)
plt.show()

"""#### K-Means clustering"""

kmeans_silhouettes = []
for n_clusters in range(2, 43):
  kmeans = KMeans(n_clusters = n_clusters, random_state=seed)
  labels = kmeans.fit_predict(x_3d)
  silhouette = silhouette_score(x_3d, labels)
  kmeans_silhouettes.append(silhouette)
plt.scatter(range(2,43), kmeans_silhouettes) 
plt.show

kmeans_silhouettes = []
for n_init in range(10, 100):
  kmeans = KMeans(n_clusters = 12,n_init=n_init, random_state=seed)
  labels = kmeans.fit_predict(x_3d)
  silhouette = silhouette_score(x_3d, labels)
  kmeans_silhouettes.append(silhouette)
plt.scatter(range(10,100), kmeans_silhouettes) 
plt.show

max_y = max(kmeans_silhouettes[4:])  # Find the maximum y value
max_x = kmeans_silhouettes.index(max_y)  # Find the x value corresponding to the maximum y value
print(max_x, max_y)

from sklearn.metrics.cluster import fowlkes_mallows_score
from sklearn import metrics
fowlkes_mallows_score([0, 0, 1, 1], [0, 0, 1, 1])
kmeans = KMeans(n_clusters = 12,n_init=50, random_state=seed)
kmeans_fit = kmeans.fit_predict(x_3d)
print('Silhouette: ', silhouette_score(x_3d, kmeans_fit))
print('Rand Index (con ground truth): ', adjusted_rand_score(y_train,kmeans_fit))
print('fowlkes_mallows_score: ',fowlkes_mallows_score(y_train, kmeans_fit))
print('completeness_score',metrics.completeness_score(y_train, kmeans_fit))
print('homogeinety completnes', metrics.homogeneity_completeness_v_measure(y_train, kmeans_fit))# esta es buena para usar con las distintas tecnicas y compararlas entre si
print('AMI',metrics.adjusted_mutual_info_score(y_train, kmeans_fit))

import matplotlib.pyplot as plt
fig= plt.figure(figsize=(15,15))
plt.scatter(x_3d[:,0],x_3d[:,1],c=kmeans_fit)
plt.show()

"""
### Resources

[Reducción de la dimensionalidad](https://aukera.es/blog/reduccion-dimensionalidad/). Aukera, 2018.

[Dimensionality Reduction in Python with Scikit-Learn](https://stackabuse.com/dimensionality-reduction-in-python-with-scikit-learn). Stack Abuse, 2019.

[Hierarchical Clustering](https://www.datanovia.com/en/lessons/agglomerative-hierarchical-clustering/). Datanovia, 2019.
"""
