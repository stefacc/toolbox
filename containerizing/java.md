# java
## image to build and run
```
# image to build with maven
FROM public.ecr.aws/docker/library/maven:3.6-jdk-11-slim AS builder
WORKDIR /app
COPY . /app
# RUN mvn clean package -DskipTests
RUN mvn compile
RUN mvn package

# image to run with amazon corretto
FROM public.ecr.aws/amazoncorretto/amazoncorretto:11
WORKDIR /app
COPY --from=builder /app/target/app-maven-1.0.0.jar /app/app-maven-1.0.0.jar
CMD "java" "-jar" "/app/app-maven-1.0.0.jar"
```
