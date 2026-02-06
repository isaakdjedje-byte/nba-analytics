# Image de base Jupyter avec Spark 3.5.0
FROM jupyter/pyspark-notebook:spark-3.5.0

# Passer en root pour les installations
USER root

# Installation Delta Lake 3.0.0 et dépendances Python
RUN pip install --no-cache-dir \
    delta-spark==3.0.0 \
    pyyaml \
    nba-api==1.1.11 \
    requests \
    pandas \
    numpy \
    pytest

# Télécharger les JARs Delta Lake 3.0.0 (delta-spark, pas delta-core)
RUN wget https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.0.0/delta-spark_2.12-3.0.0.jar \
    -O /usr/local/spark/jars/delta-spark_2.12-3.0.0.jar && \
    wget https://repo1.maven.org/maven2/io/delta/delta-storage/3.0.0/delta-storage-3.0.0.jar \
    -O /usr/local/spark/jars/delta-storage-3.0.0.jar

# Créer les répertoires de l'application
WORKDIR /app

# Créer les dossiers pour les données
RUN mkdir -p /app/data/raw /app/data/processed /app/data/exports

# Copier le projet
COPY . /app/

# Permissions
RUN chown -R jovyan:users /app

# Revenir à l'utilisateur jovyan (non-root)
USER jovyan

# Variables d'environnement Spark avec Delta
ENV SPARK_EXTRA_CLASSPATH="/usr/local/spark/jars/delta-spark_2.12-3.0.0.jar:/usr/local/spark/jars/delta-storage-3.0.0.jar"
ENV PYSPARK_SUBMIT_ARGS="--packages io.delta:delta-spark_2.12:3.0.0 pyspark-shell"

EXPOSE 8888 4040

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
