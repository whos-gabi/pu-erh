from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, date_format, to_timestamp, max as spark_max, round

# Initialize Spark
spark = SparkSession.builder.appName("PostgresAnalytics") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

jdbc_url = "jdbc:postgresql://<host>:5432/office_appointments"
properties = {
    "user": "<user>",
    "password": "<password>",
    "driver": "org.postgresql.Driver"
}

# Load appointments
df = spark.read.jdbc(url=jdbc_url, table="public.core_appointment", properties=properties)

# Convert timestamps
df = df.withColumn("start_date", to_timestamp(col("start_date")))

# Base grouping
df_grouped = df.groupBy(
    col("item_id"),
    date_format(col("start_date"), "EEEE").alias("weekday"),
    hour(col("start_date")).alias("hour")
).count()

# Find max count per item + weekday
df_max = df_grouped.groupBy("item_id", "weekday") \
    .agg(spark_max("count").alias("max_count"))

# Join and compute popularity percentage
df_final = df_grouped.join(df_max, on=["item_id", "weekday"], how="left") \
    .withColumn("popularity", round((col("count") / col("max_count")) * 100, 2)) \
    .orderBy("item_id", "weekday", "hour")

display(df_final)