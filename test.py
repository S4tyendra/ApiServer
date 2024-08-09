from database import connect_to_database


CST303 = """
## Data Communication and Computer Networks

### Data Communication Measurement

**How do we measure the effectiveness of data communication?**

There are four major parameters we use to assess the effectiveness of data communication:

1. **Performance:** This focuses on how efficiently data is transferred between two points. 
    * **Transit Time:** The time taken for data to travel from the sender to the receiver.
    * **Response Time:** The time it takes for the receiver to acknowledge the sender after receiving data.

    Performance depends on factors such as:
    * Number of users on the network
    * Medium of communication (type and capacity)
    * Capability of hardware and software involved 

2. **Reliability:** This measures the trustworthiness of the network in terms of successful data delivery. 
    * **Frequency of Failure:**  How often does the network experience data loss or errors?
    * **Recovery Time:** How long does it take for the network to recover from a failure and resume normal operation?
    * **Robustness:** The network's ability to withstand failures and continue functioning.  A robust network can handle a certain number of failures without completely breaking down.

3. **Security:** This involves protecting data from unauthorized access and ensuring only authorized users can send and receive information. 

### Categories of Networks

1. **LAN:** Local Area Network (Covers a small geographic area like a home or office)
2. **MAN:** Metropolitan Area Network (Covers a larger area like a city)
3. **WAN:** Wide Area Network (Covers a vast geographical area, even globally, like the Internet)
4. **Intranet:** A private network used within an organization. It uses Internet protocols but is accessible only to authorized users within the organization. 
5. **Extranet:** Similar to an intranet but provides controlled access to authorized users outside the organization. It's a secure way for businesses to share information with partners, vendors, or customers. 

### Client-Server Model

This model involves a **client**, which requests services or data, and a **server**, which provides those services or data. 

* **Client:** The device or software that requests data or services from the server.
* **Server:** A powerful computer that stores and manages data and responds to client requests.

The client and server can be located on the same network or on different networks.

### Peer-to-Peer Model

In this model, every device (or **peer**) on the network can act as both a client and a server.  Each peer can send data directly to other peers without a dedicated server. Examples include file-sharing networks.

### The OSI Model

**What is the OSI Model?**

The OSI (Open Systems Interconnection) model is a conceptual framework that standardizes communication between different systems in a network. It is a set of protocols or rules that any two different systems must follow to communicate with each other.

**Key Features of the OSI Model:**

1. **Flexible:** The OSI architecture is designed to be adaptable to changes and future developments. It can accommodate new technologies and protocols.
2. **Interoperable:** The OSI model promotes communication between different systems, regardless of their underlying hardware or software.
3. **Robust:** The OSI model ensures that the network can handle failures and continue operating efficiently. It can compensate for errors and data loss.

**Why is the OSI Model important?**

The OSI model is crucial because it provides a common language and framework for networking professionals to understand and design networks. It ensures compatibility and interoperability between different systems, allowing them to work together seamlessly.  Without the OSI model, communication between devices from different vendors or using different technologies would be incredibly difficult. 


![](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_b1f1121a2b6cba6bbbc5e490942599f5)
![](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_9d95a624b2a4851366989c130d2d8d5c)
"""
CST303_intro = ["Performance", "Reliability", "Security", "LAN", "MAN", "WAN", "Intranet", "Extranet", "Client-Server", "Peer-to-Peer"]
CST307 = """
# Machine Learning: Introduction

## What is Machine Learning (ML)?

Machine learning is a type of artificial intelligence (AI) that allows software applications to become more accurate in predicting outcomes without being explicitly programmed to do so. Machine learning algorithms use historical data as input to predict new output values.

## Applications of Machine Learning

* **Spam filtering:** Google identifies spam emails by looking for certain words. These words are defined based on user reports of spam. If those words are present in an email, it gets flagged as spam.
* **Credit card fraud detection:** Large or unusual transactions might be flagged for fraud detection. The system may contact you to verify the transaction.
* **Digit recognition on checks:** Checks are scanned to identify the handwritten digits and amount, regardless of individual handwriting variations.
* **MRI image analysis:** Doctors use MRI images to identify the extent of diseases and determine treatment based on the image analysis.
* **Search engines:** Google search engine displays results based on your search history and preferences.
* **Handwriting recognition:** Used for processing handwritten documents, like bank checks.
* **Scene classification:**  Categorizing images based on content such as parks, scenery, mountains, etc.
* **Recommendation system:**  Recommending products or services based on user preferences and past purchases.

## Machine Learning vs. Statistics

Machine learning borrows heavily from statistics.  It uses statistical methods for:

* **Exploratory data analysis:** Initial analysis of data to identify patterns.
* **Hypothesis testing:** Testing assumptions about the data. For example:
    * **Null hypothesis:** The original assumption about the data, such as the average performance of students being 70%.
    * **Alternative hypothesis:** A new hypothesis proposed based on changes in the data, such as the average performance increasing after using a projector in class. 

ML also uses other methods beyond statistics, such as decision trees, neural networks, and support vector machines.

## Machine Learning Methods

* **Decision tree:** A tree-like structure used to classify data. Data is divided into branches based on different attributes until a final decision is reached.
* **Random Forest:** Builds multiple decision trees and combines their results to improve accuracy and prevent bias.
* **Rule induction:** Uses "if-then-else" conditions to classify data.
* **Neural networks:** Mimics the human brain to learn from data. Errors are fed back into the system to improve the results.
* **Support vector machines:** Finds the optimal boundary between different classes of data.
* **Clustering methods:** Grouping similar data points together without pre-defined labels. For example, forming friend groups within a class based on shared habits and interests.
* **Association rules:** Identifying relationships between different items. For example, in a supermarket, placing items together that are frequently purchased together, like bread and butter.
* **Feature selection:** Selecting the most important attributes of data to improve efficiency and accuracy.

## Types of Machine Learning

### Supervised Learning

* Uses labeled data where the output is known.
* Requires a supervisor to label the data.
* Examples:
    * Predicting a student's grade (A, B, C) based on their midterm and quiz marks.
    * Classifying fruits (banana, orange, apple) based on their length, width, and weight.
    * Predicting whether a person will purchase a laptop based on their profession, education, age, and salary.
* Methods:
    * **Classification:** Categorizing data into discrete groups (e.g., yes/no, 0/1, +1/-1).
        * **Binary classification:** Two groups (e.g., purchase/not purchase).
    * **Regression:** Predicting a continuous output (e.g., marks, percentage, price).

### Unsupervised Learning

* Uses unlabeled data where the output is unknown.
* No supervisor is needed to label the data.
* Examples:
    * Clustering students into friend groups based on their similarities.
    * Grouping customers based on their purchasing patterns in a supermarket.
* Methods:
    * **Clustering:** Grouping similar data points together (e.g., k-means, Gaussian mixtures, spectral clustering, hierarchical clustering).

### Reinforcement Learning

* Learning from the environment through rewards and punishment.
* No labeled data is needed.
* The agent learns by interacting with the environment and receiving feedback.
* Examples:
    * A child learning to place toys at the proper place by being praised (reward) or scolded (punishment).
    * A robot learning to navigate a maze by being rewarded for reaching the goal and penalized for hitting walls.

## Key Concepts

* **Training data:** Historical data used to train the machine learning model. It represents previous experiences.
* **Experience:** Previous data used to learn and improve the model.
* **Performance measure:** Metrics used to evaluate the performance of the machine learning model (e.g., accuracy, precision, recall).
* **Task:** The problem that the machine learning model is trying to solve (e.g., classification, regression, clustering).
* **Algorithm:** The specific method used to train the machine learning model (e.g., decision tree, neural network, support vector machine).

## Steps in Machine Learning

1. **Data collection and preparation:** Gathering relevant data and cleaning it for analysis.
2. **Feature selection:** Identifying the most important attributes of the data.
3. **Model selection:** Choosing the appropriate algorithm based on the data and task.
4. **Model training:** Training the model using the training data.
5. **Model evaluation:** Evaluating the performance of the model using a performance measure.
6. **Model deployment:** Deploying the trained model to make predictions on new data.

## Conclusion

Machine learning is a powerful tool with a wide range of applications. Understanding the different types of machine learning, the key concepts, and the steps involved can help us to apply these techniques effectively to solve real-world problems.

![20240808_101625.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_31ec6df84934b40a6d2b98604a91e4e9)
![20240808_104000.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_16abe8c42fd75b4e2637dbc34c14aa36)
![20240808_100858.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_f4277caf47c94076bff531cf796f3f7e)
![20240808_104130.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_c0a9dfa9cbae9ba0b4ec6fdf224cac22)
![20240808_104928.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_f95bffc5a8ff4e1176b05fd14b8501fe)
![20240808_103510.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_351dc1ab33707f88cebdef0695f3c83d)
![20240808_104243.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_7956b23dc23bf6affc59c0b1d1bdf3a6)
![20240808_104216.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_f74dc13411f81d522d794ec61a0036ab)
![20240808_104830.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_558310c0479e514a57492c1ef49ebc0e)
![20240808_101536.jpg](https://yawning-guppy-devh-in-fa2b7e58.koyeb.app/file/1717833294392072_ba441f5e97fd13c1f9a326720c47b327)

"""
CST307_intro=["Learning", "Algorithms", "Data", "Prediction", "Accuracy", "Applications", "Methods", "Types", "Concepts", "Steps"]


date = "2024-08-08"

doc_to_be_inserted = {
    "_id":date,
    'CST307':CST307,
    'CST303':CST303,
    'CST303_intro': CST303_intro,
    'CST307_intro': CST307_intro
}

async def main():
    db =await connect_to_database('notes')
    db.iiitkota.insert_one(
        doc_to_be_inserted
    )
    
import asyncio

asyncio.run(main())