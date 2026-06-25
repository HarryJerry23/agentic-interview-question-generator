# Introduction to Google Colab


## 1. Google Colab

**Colab** is a **free, cloud-based platform** provided by Google that allows us to **write and execute Python in the browser**.


## 2. Features of Google Colab


- **Zero configuration required**  
  - No setup or installation is needed as it runs entirely in the cloud.
- **Free access to GPUs **  
  - Provides access to hardware like **GPUs** and **TPUs** (limited) for computationally intensive tasks.
- **Easy sharing and collaboration**
  - Notebooks can be stored in **Google Drive**.
  - Can be easily shared with others.
  
- **Pre-installed libraries**
  - Many popular Python libraries come pre-installed.


## 3. Setting Up Colab

To start using **Google Colab**:

1. Open a browser and go to:  
   `https://colab.research.google.com`
2. Sign in with your **Google account**.
3. Click **“New Notebook”** to start.

> If you are already logged in, Colab will open directly.

## 4. Writing First Python Code in Colab

In Colab, you will work with **cells**:

- **Code cell**
- **Output cell**

You write Python code in the **code cell**, click the **Run button**, and see the result in the **output cell**.


## 5. Working With Notebooks

- Your notebooks **save to Google Drive automatically**.
- Variables defined in **one cell** can later be used in **other cells**.
- A **change in one cell** will reflect in other cells on **rerun**.

## 6. Experiment with Colab

Start experimenting and learning with **Google Colab notebooks**.

Use Colab to:

- Try out Python code
- Practice and explore concepts"
<iframe src="https://llmappsroadmap.niat.tech/" width="100%" height="580" frameborder="0" marginwidth="0" marginheight="0" scrolling="yes" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen></iframe>

---

# Introduction to Third-Party Packages in Python


## 1. Introduction to Third-Party Packages


- **Third-party packages** are software libraries developed by **external developers**.  
- They help **save time and effort** while building applications.
- These packages provide **additional functionality** that can be easily integrated into your own software projects.

## 2.Python Packages 


- **Third-party packages** are like **downloading new apps** that add **extra functionality** to Python.


### 2.1 Packages and Modules

- **Module**  
  - A **Python file** containing code with functions, classes, etc.
- **Package**  
  - A **collection of modules**.  
  - You can think of a package like a **folder** that contains multiple files (modules).

## 3. Third-Party Packages in Python – Examples

Python provides multiple packages to make development **faster**:

- requests
- pygame
- matplotlib
- pytorch
- tensorflow

These packages help in different areas such as **web requests**, **game development**, **data visualization**, and **machine learning**.


## 4. Introduction to API Calls in Python

### 4.1 Requests Package

- The **Python `requests` package** is used for **making HTTP requests** to a specified URL.
- It allows your Python program to **communicate with web servers** and work with **APIs**.


### 4.2 Installing `requests`

To install the `requests` package, run the following command in the **terminal/command prompt**:

```bash
!pip install requests
```


### 4.3 PIP and PyPI

* **PIP**

  * Python packages are typically installed via the Python package manager **`pip`**.
  * `pip` pulls libraries from repositories like **PyPI**.

* **PyPI (Python Package Index)**

  * PyPI is like a **big library or catalog** that holds thousands of Python packages.
  * Whenever you want to add new functionality to your Python programs, you can usually find a suitable package on **PyPI**.


## 5. Building a Simple Weather Application

### 5.1 Real-Time Weather Updates

We will build a simple **weather application** that displays the **current weather** of a given location.


### 5.2 Weather API URL

To get the weather information of **Mumbai**, we will use a **weather API URL**:

```python
url = ""https://api.weatherapi.com/v1/current.json?key=e942dbeb75424295b4e94030242510&q={location}""
```

We will make an **API call** to this URL using the **`requests`** package.


### 5.3. Making a GET Request Using `requests`
* `requests.get()` is used to send a **GET request** to a specified URL for **retrieving data** from a server.

Basic syntax:

```python
requests.get(url, params, **kwargs)
```

* `url`: The URL of the resource.
* `params`: optional
* `kwargs`: optional


### 5.4 Making a GET Request

```python
import requests

# Getting weather data of Mumbai
url = ""https://api.weatherapi.com/v1/current.json?key=e942dbeb75424295b4e94030242510&q=Mumbai""

response = requests.get(url)
```

Here:

* We import the `requests` package.
* Set the `url` for the weather API.
* Use `requests.get(url)` to send a GET request.


### 5.5. Understanding the Response Object

#### 5.5.1 Response Object

* `requests.get()` returns a **response object**.
* This object contains all the **data returned from the server** in response to the HTTP request.

#### 5.5.2 Response Object Data


* `.json()`

  * Parses the response payload as **JSON** and returns a **dictionary**.
* `.status_code`

  * Represents the **HTTP status code**.
* `.text`

  * Returns the **content** of the response as **Unicode text**.
* `.reason`

  * Textual reason for the HTTP status, e.g., `""Not Found""` or `""OK""`.
* `.headers`

  * A dictionary-like object containing the **response headers**.
* `.url`

  * The **URL** of the response.


### 5.6 Accessing JSON Data from the Response

#### 5.6.1 Using `.json()`

```python
import requests

# Getting weather data of Mumbai
url = ""https://api.weatherapi.com/v1/current.json?key=e942dbeb75424295b4e94030242510&q=Mumbai""

response = requests.get(url)
data = response.json()

print(data)
```

* `response.json()` converts the response into a **Python dictionary**.
* `data` now holds all the weather information returned by the API.


### 5.7. Printing the Current Temperature

We can access specific fields from the JSON data, such as the **current temperature**:

```python
import requests

# Getting weather data of Mumbai
url = ""https://api.weatherapi.com/v1/current.json?key=e942dbeb75424295b4e94030242510&q=Mumbai""

response = requests.get(url)
data = response.json()

print(f""Temperature: {data['current']['temp_c']}°C"")
```

**Output:**

```text
Temperature: 29.1°C
```

## 6. Other Third-Party Packages in Python

In addition to `requests`, Python has many other useful third-party packages, such as:

### 6.1 pygame
* `pygame` – used to **design and build games** using Python

    * To install `pygame`:
    
      ```bash
      !pip install pygame
      ```

### 6.2 matplotlib

* `matplotlib` – an **open-source plotting package** for data visualization
   
    * To install `matplotlib`:

    ```bash
    !pip install matplotlib
    ```

## 7. Other useful python packages

* pytorch
* tensorflow
* Tkinter
* NumPy
* Pandas
* Pillow
* Scikit-learn
* Beautiful Soup"


---

# Introduction to Flask

In previous units, we explored third party packages in Python. Now, we'll learn how to create the web applications that can power them. In this unit, we will learn about Flask, a popular Python framework used for building web applications and APIs. We will start from the basics and build our very first web application.

## Setting up Code Environment

To follow along with this material and develop Flask applications, you'll need to set up your development environment. This primarily involves installing Python and a suitable code editor like VS Code.

## 1. Install Python

Python is the programming language that Flask is built upon.

*   **Download Python:**
    *   Visit the official Python website: <a href=""https://www.python.org/downloads/"" target=""_blank"">https://www.python.org/downloads/</a>

    *   Download the latest stable version of Python for your operating system (Windows, macOS, Linux).
*   **Install Python:**
    *   **Windows:** Run the installer. Make sure to check the ""Add Python X.X to PATH"" option during installation. This is crucial for running Python commands from your terminal.
    *   **macOS:** Python might be pre-installed, but it's recommended to install the latest version from the official website or using a package manager like Homebrew (`brew install python`).
    *   **Linux:** Python is usually pre-installed. You can update it using your distribution's package manager (e.g., `sudo apt-get install python3` for Debian/Ubuntu).
*   **Verify Installation:** Open a new terminal or command prompt and type:

    ```bash
    python --version
    ```
    or
    
    ```bash
    python3 --version
    ```
    You should see the installed Python version.

## 2. Install Visual Studio Code (VS Code)

VS Code is a popular, lightweight, and powerful code editor that provides excellent support for Python development.

*   **Download VS Code:**
    *   Visit the official VS Code website: <a href=""https://code.visualstudio.com/"" target=""_blank"">https://code.visualstudio.com/</a>
    *   Download the installer for your operating system.
*   **Install VS Code:**
    *   Run the installer and follow the instructions. It's generally recommended to keep the default settings.
*   **Install Python Extension for VS Code:**
    *   Open VS Code.
    *   Go to the Extensions view by clicking on the square icon on the sidebar or pressing `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (macOS).
    *   Search for ""Python"" and install the extension provided by Microsoft. This extension provides features like IntelliSense, linting, debugging, and more.

With Python and VS Code set up, you're ready to start building your Flask applications!

## Python: A Versatile Language
Python is a programming language known for its simplicity, readability, and versatility. It is used in almost every field and is a widely used programming language that can be used for both frontend and backend development. The capacity of the computer of performing more than one task at the same time is called the versatility.

### Python can be used in:
- **AI / Machine Learning**
- **Big Data**
- **Smart Device / IOT**
- **Game Developement**
- **Backend Developement**

## Python in Web Applications

Python is a versatile programming language known for its simplicity and readability. It's used in nearly every field, including web development, where it can be used for both frontend and backend tasks.

### Python Frameworks

A Python framework is a collection of tools and libraries that provide a common structure to build applications more quickly and efficiently. They offer reusable code and a defined architecture so you don't have to start from scratch.

### Popular Python frameworks include:

- **Flask**
- **Django**
- **FastAPI**
- **CherryPy**


## Flask

Flask is mainly used for building Web Applications and RESTful APIs.

- **Popularity:** Flask is one of the most popular and widely used web frameworks by developers, according to developer surveys.
- **Companies Using Flask:** Major companies like **Netflix, CRED, Reddit, and Lyft** use Flask to power their applications.

### Installing Flask

Just like any other Python package, Flask can be installed using `pip`.

Open your terminal and run the following command:

```bash
    pip install flask
```

## Building Your First Flask Application

Let's build a simple web application that responds with ""Hello World!"" when a user visits it.

### The Flow
1.  A **Client** (like a web browser) sends an HTTP Request to a URL.
2.  Our **Flask Server** receives the request.
3.  The server processes the request and sends back an HTTP Response containing the text ""Hello World!"".

<details>
<summary><strong>Step 1: Create a Python File</strong></summary>
<br>
Create a new Python file and name it `hello_world.py`.
</details>

<details>
<summary><strong>Step 2: Write the Flask Code</strong></summary>
<br>
Add the following code to your `hello_world.py` file. Each part is explained below.

```python
# 1. Import the Flask class
from flask import Flask

# 2. Create an instance of the Flask class
app = Flask(__name__)

# 3. Define a route and the function to handle it
@app.route('/', methods=['GET'])
def home():
   return ""Hello World!""

# 4. Run the application server
if __name__ == '__main__':
    app.run(debug=True)
```

**Code Explained:**

1.  **`from flask import Flask`**: This line imports the main `Flask` class from the `flask` package.
2.  **`app = Flask(__name__)`**: This creates an instance of the Flask application. `__name__` is a special Python variable that gives Flask information about where the application is located. The `app` variable represents our web application.
3.  **`@app.route('/', methods=['GET'])`**: This is a decorator that tells Flask which URL should trigger our function.
    -   The first argument (`'/'`) is the **path** of the URL (the root of our website).
    -   The `methods` argument specifies which HTTP methods this route responds to. If not specified, it defaults to `GET`.
4.  **`def home(): ...`**: This is the function that will be executed when a user visits the `/` route. It returns the string ""Hello World!"", which will be sent back to the browser.
5.  **`app.run(debug=True)`**: This line starts the Flask development server.
    -   `debug=True` is a helpful parameter that automatically reloads the server when you make code changes and provides detailed error pages if something goes wrong.

</details>

<details>
<summary><strong>Step 3: Run the Flask Server</strong></summary>
<br>
To start your application, open a terminal in the same directory as your `hello_world.py` file and run the following command:

```bash
python hello_world.py
```

You will see output indicating that the Flask server is running and listening for connections, typically on `http://127.0.0.1:5000/`.

</details>

<details>
<summary><strong>Step 4: Access Your Application</strong></summary>
<br>
Open your web browser and navigate to `http://127.0.0.1:5000/`. You should see the ""Hello World!"" message displayed on the page.

</details>


## Flask Routing

Routing is the process of mapping URLs to specific functions. You can define multiple routes in your application.

Let's add another route that responds with a name.

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
   return ""Hello World!""

# New route for the path '/name'
@app.route('/name')
def get_name():
   return ""Rahul""

if __name__ == '__main__':
    app.run(debug=True)
```

Now, if you run the server and visit `http://127.0.0.1:5000/name`, the browser will display ""Rahul"".


# Building Rest APIs using Flask

In the previous unit, we learned the fundamentals of Flask by building a simple web application. Now, we will take the next step and use Flask to build a **REST API**. We'll create several endpoints to manage a list of products, simulating a real-world e-commerce application like Zepto.


## What is an API?

An **API (Application Programming Interface)** is a software intermediary that allows two applications to talk to each other. While a user interacts with a website through its User Interface (buttons, forms), applications and servers interact with each other through APIs.

For our project, we will build a few APIs for a ""Zepto Clone"" to manage product data.

### APIs We Will Build:
- **Get Products**: Fetches a list of all available products.
- **Get a Single Product**: Fetches the details of one specific product using its ID.
- **Add a Product**: Adds a new product to our list.

### API Testing Tools
To test our API endpoints, we need a special tool. While there are many options like Insomnia and Swagger, we will use **Postman**, one of the most popular tools for API testing.

> **Action:** Before you begin, please create a free account on [Postman](https://www.postman.com/) and create a new, empty workspace.


## 1. Get All Products API

Our first endpoint will return a list of all products.

<details>
<summary><strong>Step 1: Setting up Sam
In this unit, we successfully built a basic REST API using Flask, covering essential operations like fetching all products, retrieving a single product by ID, and adding new products.ple Data</strong></summary>
<br>
First, let's create a new `app.py` file. In a real application, this data would come from a database, but for now, we'll use a simple Python list of dictionaries as our sample data.

```python
from flask import Flask

app = Flask(__name__)

# Sample product data
products = [
   {""id"": 1, ""name"": ""Chopping Board"", ""price"": 360},
   {""id"": 2, ""name"": ""Sketch Pens"", ""price"": 30},
   {""id"": 3, ""name"": ""Shoes"", ""price"": 519}
]

if __name__ == '__main__':
    app.run(debug=True)
```
</details>

<details>
<summary><strong>Step 2: Creating the GET /products Route</strong></summary>
<br>
Now, let's create the Flask route that will return our list of products. Flask automatically converts Python lists returned from routes into JSON responses.

```python
from flask import Flask

app = Flask(__name__)

products = [
   {""id"": 1, ""name"": ""Chopping Board"", ""price"": 360},
   {""id"": 2, ""name"": ""Sketch Pens"", ""price"": 30},
   {""id"": 3, ""name"": ""Shoes"", ""price"": 519}
]

## Route to get all products
@app.route('/products', methods=['GET'])
def get_products():
  return products

if __name__ == '__main__':
    app.run(debug=True)
```
</details>

<details>
<summary><strong>Step 3: Testing with Postman</strong></summary>
<br>
1.  Run your Flask application: `python app.py`.
2.  Open Postman and create a new request.
3.  Set the request method to **GET**.
4.  Enter the URL: `http://127.0.0.1:5000/products`.
5.  Click **Send**.

You should see the JSON array of products in the response body.
</details>


## 2. Get a Single Product API

Next, we'll create an endpoint to fetch a single product by its unique ID.

<details>
<summary><strong>Step 1: Understanding Path Parameters</strong></summary>
<br>
To identify a specific product, we need to pass its ID in the URL. We can achieve this using a **path parameter**. The URL will look like this: `/products/<product_id>`.

Flask will capture the value from the URL and pass it as an argument to our view function.

Examples:

- `/products/1` will fetch the product with `id = 1`.
- `/products/3` will fetch the product with `id = 3`.
</details>

<details>
<summary><strong>Step 2: Implementing the Route</strong></summary>
<br>
Let's add the new route to our `app.py`. The function will loop through the `products` list to find a match.

> **Note:** By default, URL parameters are strings. Since our product IDs are integers, we need to convert `product_id` to an `int` before comparing.

```python
# ... (previous code remains the same)

# Route to get a single product by ID
@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
  product_id = int(product_id)
  for product in products:
    if product['id'] == product_id:
      return product
  # Return an error if the product is not found
  return {""error"": ""Product not found""}, 404

# ... (app.run remains the same)
```
</details>

<details>
<summary><strong>Step 3: Testing the Endpoint</strong></summary>
<br>
1.  Make sure your Flask server is running.
2.  In Postman, create a new **GET** request.
3.  Enter the URL for a specific product, for example: `http://127.0.0.1:5000/products/2`.
4.  Click **Send**.

</details>


## 3. Add a New Product API

Finally, let's create a **POST** endpoint to add a new product to our list.

<details>
<summary><strong>Step 1: Understanding the Request Body</strong></summary>
<br>
When creating a new resource, the client needs to send the data for that resource. This data is sent in the **request body**, typically in JSON format.

A sample JSON request body to add a new product would look like this:

```json
{
  ""name"": ""Laptop Bag"",
  ""price"": 800
}
```
</details>

<details>
<summary><strong>Step 2: Using the 'request' Object</strong></summary>
<br>
To access incoming request data in Flask, we need to import the `request` object. The `request.get_json()` method will parse the JSON body from the request and return it as a Python dictionary.

Update your imports to include `request`.

```python
from flask import Flask, request
```
</details>

<details>
<summary><strong>Step 3: Implementing the POST Route</strong></summary>
<br>
This route will listen for `POST` requests on the `/products` endpoint. It will read the new product data, assign it a new ID, and add it to our list.

```python
# ... (previous code remains the same)

# Route to add a new product
@app.route('/products', methods=['POST'])
def add_product():
   new_product = request.get_json()
   
   # Generate a new ID (in a real app, a database would handle this)
   new_product['id'] = len(products) + 1
   products.append(new_product)
   
   return {""message"": ""Product added!"", ""product"": new_product}, 201

# ... (app.run remains the same)
```
</details>

<details>
<summary><strong>Step 4: Testing the POST Endpoint</strong></summary>
<br>
1.  Make sure your Flask server is running.
2.  In Postman, create a new request.
3.  Set the method to **POST** and the URL to `http://127.0.0.1:5000/products`.
4.  Go to the **Body** tab, select **raw**, and choose **JSON** from the dropdown.
5.  Paste the new product JSON into the text area:

    ```json
    {
      ""name"": ""Laptop Bag"",
      ""price"": 800
    }
    ```
6.  Click **Send**.

You should receive a ""Product added!"" message. You can verify this by making another `GET` request to `/products` to see the newly added item in the list.
</details>


## Conclusion

In this unit, we successfully built a basic REST API using Flask, covering essential operations like fetching all products, retrieving a single product by ID, and adding new products.
---

# Integrating Flask APIs in Frontend

In the previous session, we created a **Flask API backend** for a Zepto-like app. We built API endpoints such as **`/products`** and **`/product/<id>`** to fetch product data, and tested the responses using **Postman**.

In this session, we are going to build **NxtExpress**, an e-commerce web page that showcases products with **images, prices, and descriptions**. The project is already partially built with HTML, CSS, and JavaScript, but the **frontend is not yet connected** to the backend API.

---

## NxtExpress - An E-commerce Webpage

The main goal of this session is to **integrate our existing NxtExpress UI with the Flask API** so that product data is fetched **dynamically** and displayed beautifully as **interactive product cards**.

---

### Prerequisite

- **VS Code**  
- **Python**  
- **Flask**

---


### Session Initial Code

The session’s initial code contains both the **frontend** and **backend** inside the same project folder:  

- **Backend — Flask API:** Handles API routes  
- **Frontend — UI:** Built with HTML, CSS, and JavaScript to display product cards  
- **Resource.md:** Contains the required JSON data  

Download session initial code : <a href=""https://nkb-backend-ccbp-media-static.s3-ap-south-1.amazonaws.com/ccbp_beta/media/content_loading/uploads/dcb093a3-b8ea-420a-ada5-d6d0d1e4f010_Nxt_Express.zip"" target=""_blank"" >NxtExpress Initial Code</a>

When we run this code in the browser, we won’t see any product cards because the frontend is **not yet connected** to the backend.  

What we are going to build next is the **integration of the frontend with the Flask API** so that the UI displays real product data as **product cards**.

---

### Steps to Integrate Flask APIs with Frontend
<details> 
<summary>**Update Products Data in Flask**</summary>

- We will add more products with **description** and **image** fields.  
- This JSON data is provided in **Resource.md**.

```json
[
  {
    ""id"": 1,
    ""name"": ""Chopping Board"",
    ""price"": 360,
    ""description"": ""A durable wooden chopping board for daily kitchen use."",
    ""image"": ""https://bit.ly/3XCmlH5""
  },
  {
    ""id"": 2,
    ""name"": ""Sketch Pens"",
    ""price"": 30,
    ""description"": ""12 bright colors perfect for school and art projects."",
    ""image"": ""https://bit.ly/3X8Tb2d""
  },
  {
    ""id"": 3,
    ""name"": ""Shoes"",
    ""price"": 519,
    ""description"": ""Comfortable running shoes with breathable mesh."",
    ""image"": ""https://bit.ly/4r5FnTX""
  },
  {
    ""id"": 4,
    ""name"": ""Water Bottle"",
    ""price"": 199,
    ""description"": ""1-litre stainless steel insulated bottle."",
    ""image"": ""https://bit.ly/48oQWy3""
  },
  {
    ""id"": 5,
    ""name"": ""Notebook"",
    ""price"": 85,
    ""description"": ""200-page ruled notebook for study & office use."",
    ""image"": ""https://images.unsplash.com/photo-1519682337058-a94d519337bc""
  },
  {
    ""id"": 6,
    ""name"": ""Earphones"",
    ""price"": 299,
    ""description"": ""High-quality wired earphones with mic."",
    ""image"": ""https://bit.ly/4i705i2""
  },
  {
    ""id"": 7,
    ""name"": ""Backpack"",
    ""price"": 899,
    ""description"": ""Lightweight waterproof backpack with 3 compartments."",
    ""image"": ""https://bit.ly/4ocvZuZ""
  },
  {
    ""id"": 8,
    ""name"": ""LED Bulb"",
    ""price"": 120,
    ""description"": ""9W energy-efficient LED bulb."",
    ""image"": ""https://bit.ly/49oKyI9""
  },
  {
    ""id"": 9,
    ""name"": ""Coffee Mug"",
    ""price"": 250,
    ""description"": ""Ceramic mug with heat insulation and stylish print."",
    ""image"": ""https://bit.ly/48uDdov""
  },
  {
    ""id"": 10,
    ""name"": ""Keyboard"",
    ""price"": 750,
    ""description"": ""USB keyboard with smooth keys and long durability."",
    ""image"": ""https://bit.ly/3X6DtEU""
  }
]

```
</details> <details> 
<summary>**Run Flask API in VS Code and Copy the Endpoint URL**</summary>

- Open **backend folder**  
- Inside it, create **app.py**  

**Add Flask Code**

- Add below Flask code in app.py
- Update products data with the new JSON data provided.

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Add new JSON data
products = [
    {...},{...},...
]

@app.route('/products')
def get_products():
    return products

app.run(debug=True)

```

### ** Frontend and Backend Cannot Talk to Each Other**

- Our frontend and backend **run on different ports/domains**, so the **browser blocks the API request** , and the products do not load on the page.
- Result: **API call fails**, products do not load, and the console shows **CORS errors**.

---

### **Turn On CORS**

To allow the frontend and backend to communicate, we need to **enable CORS** in the backend.

---

### **What is CORS?**

**CORS (Cross-Origin Resource Sharing)** allows the backend to **give permission** to the frontend so it can access data.

<details><summary>**Steps to Enable CORS**</summary>

- **Install Required Package**




```bash
pip install flask-cors
```

- **Apply CORS in Flask**

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows all origins by default


...
```
</details>
### ** Run the Flask App**

```bash
python3 app.py
```



### **Access API**

- Flask server runs at : **http ://127.0.0.1:5000/**

- Get API endpoint: **http ://127.0.0.1:5000/products**

- Test in browser → **JSON data of products will be returned**

</details> <details> <summary>**Connect Frontend to Flask Using Fetch API**</summary>
- We will add our public API endpoint as a parameter and send a **GET request** to the backend using the **JavaScript Fetch API**.

```JavaScript
async function fetchProducts() {
    try {
        const response = await fetch('http://127.0.0.1:5000/products');
        if (!response.ok) throw new Error('Failed to fetch');
        const products = await response.json();
        renderProducts(products);
    } catch (error) {
        console.warn('Failed to fetch products:', error);
        renderProducts([]);
    }
}
```

</details>
The existing HTML, CSS, and JavaScript will be used to dynamically create product cards that will be displayed in the UI."

---


# Building LLM Applications using Python | Part 1

## Introduction

So far, we have understood what LLMs are and have explored their different capabilities using no-code tools like n8n, ChatGPT, Google Gemini, and Stable Diffusion. These tools are excellent for automating workflows without writing any code.

However, sometimes we require more flexibility, control, and the ability to build custom features. This is where programming languages like Python come in. This unit will introduce you to building your first LLM-powered application using Python.

---

## Why Use a Programming Language?

While no-code tools are powerful, building applications with code provides:

-   **More Flexibility**: Integrate with any API or service you want.
-   **More Control**: Build custom User Interfaces (UIs) for your chatbots and add detailed logging for enhanced debugging.

### n8n vs Code

<details>
<summary><strong>When to use n8n</strong></summary>

-   Quick prototypes needed in hours.
-   Simple, straightforward workflows.
-   Non-technical team members need to maintain it.
</details>

<details>
<summary><strong>When to use Python</strong></summary>

-   Custom logic is required.
-   Complex error handling is necessary.
-   You need to deploy at scale for customer-facing applications.
</details>

---

## What We're Building: An AI Study Assistant

We will build an AI-powered Study Assistant that:

-   Explains complex topics in simple words.
-   Answers your questions in natural language.
-   Works anytime you need help.

---

## How Applications Talk to LLMs

Connecting to a Large Language Model (LLM) involves three main methods:

1.  Running LLMs locally on your machine.
2.  Making direct HTTP requests to an LLM's API endpoint.
3.  Using packages/libraries provided by the LLM provider.

We will be using the third method, as it's the most common and efficient approach used by developers.

### Advantages of Using Libraries

-   Removes unnecessary manual steps like formatting raw HTTP calls.
-   Handles authentication and errors internally.
-   Allows us to focus on building the actual application.

### The Three Essential Components

Building an LLM application is like making a burger. You need three key ingredients:

1.  **The Brain (LLM)**: The AI model that understands and generates text.
2.  **The Connector (API)**: The link between your application and the LLM.
3.  **Your Instructions (Prompt)**: The instructions for the LLM to perform a specific task.

---

## Python Packages for LLMs

LLM providers typically offer official Python packages (SDKs) to make integration seamless. These packages handle things like authentication, request formatting, and error handling so you can focus on building.

Here are a few popular ones:

-   `google-genai`: For Google's Gemini family of models.
-   `openai`: For OpenAI's GPT models (e.g., GPT-4).
-   `anthropic`: For Claude models (e.g., Sonnet, Opus).
-   `deepseek-ai`: For DeepSeek models.

For our project, we will use the `google-genai` package because Gemini offers a generous free tier, allowing us to build and experiment without cost.

<MultiLineNote>
Learning to use one of these packages makes it much easier to use others. Once you learn to drive one car, you can easily switch and drive another.
</MultiLineNote>

---

## Let's Build our Study Assistant

We'll use Google Colab for this project and the `google-genai` package to interact with the Gemini LLM.

<details>
<summary><strong>Step 1: Setting Up The Environment</strong></summary>

1.  Go to <a href=""https://colab.research.google.com/"" target=""_blank"" rel=""noopener noreferrer"">Google Colab</a>
2.  Create a new notebook and name it `ai_powered_study_assistant.ipynb`.
3.  Install the Google Gemini package by running the following command in a cell:

    ```python
    !pip install -U google-genai
    ```

    -   `!` tells Colab to execute this as a shell command.
    -   `pip` is the Python Package Installer.
    -   `-U` flag updates the package to the latest version if it's already installed.

</details>

<details>
<summary><strong>Step 2: Get Your API Key</strong></summary>

1.  Go to <a href=""https://aistudio.google.com/app/apikey"" target=""_blank"" rel=""noopener noreferrer"">Google AI Studio</a>
2.  Sign in and create a new API key.
3.  Copy the key. We'll need it soon.

</details>

<details>
<summary><strong>Step 3: Securely Store the API Key in Colab</strong></summary>

To avoid pasting your API key directly in the code, we'll use Colab's ""Secrets"" feature.

1.  Click the **key icon** in the left sidebar of your Colab notebook.
2.  Click **""Add new secret""**.
3.  Enter the name as `GEMINI_API_KEY`.
4.  Paste your copied API key into the ""Value"" field.
5.  Make sure the ""Allow notebook access"" toggle is enabled.

</details>

<details>
<summary><strong>Step 4: Write the Python Code</strong></summary>

Now, let's write the code to connect to the Gemini API and build our study assistant.

#### **Import Libraries and Access the API Key**

```python
import google.generativeai as genai
from google.colab import userdata

# Fetch the API key from Colab secrets
api_key = userdata.get(""GEMINI_API_KEY"")

# Initialize the Gemini client
client = genai.configure(api_key=api_key)
```

#### **Create the Study Assistant Function**

This function will take a user's prompt, send it to the Gemini model, and return the response.

```python
def study_assistant(user_prompt):
  """"""
  Sends a prompt to the Gemini model and gets a response.
  """"""
  model = genai.GenerativeModel('gemini-2.5-flash')
  response = model.generate_content(user_prompt)
  return response.text

```
- `genai.GenerativeModel('gemini-2.5-flash')`: Specifies which model to use.
- `model.generate_content(user_prompt)`: Sends the actual prompt to the LLM.
- `response.text`: The response object contains more than just the text; we extract only the text part.

#### **Call the Function and Print the Output**

```python
# Ask the study assistant a question
user_question = ""Explain Generative AI in simple terms""
output = study_assistant(user_question)

# Print the result
print(output)
```

</details>

<details>
<summary><strong>Full Working Code -Using google-genai</strong></summary>

Here is the complete code you can run in your Google Colab notebook.

```python
from google import genai
from google.colab import userdata

client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))

def study_assistant(user_prompt):
  response = client.models.generate_content(
    model=""gemini-2.5-flash"",
    contents=user_prompt
  )
  return response

output = study_assistant(""Explain Generative AI"")
print(output.text)


```
</details>

<details>
<summary><strong>Full Working Code -Using groq</strong></summary>
    
- Similar to `google-genai`, `groq` is another package that allows you to make API calls to various models. Below is an example code snippet using `groq`.
- To use Groq, you first need to install the Groq package. You can install `groq` using the following command:

```bash
pip install groq
```

```python
from groq import Groq
from google.colab import userdata

client = Groq(api_key=userdata.get(""GROQ_API_KEY""))

def study_assistant(user_prompt):
    response = client.chat.completions.create(
        model=""llama-3.1-8b-instant"",   # You can change with any Groq model
        messages=[
            {""role"": ""user"", ""content"": user_prompt}
        ]
    )
    return response

output = study_assistant(""Explain Generative AI"")
print(output.choices[0].message.content)
```

The Groq response object contains the model’s generated output along with useful metadata like token usage. You can access the final text message using `response.choices[0].message.content`.
</details>



You have built your first LLM-powered application using Python! This may be a simple version, but it’s the foundation for everything we will build next.

---

# Building LLM Applications using Python | Part 2

## Introduction

In previous session, we built a basic study assistant that could answer questions using a Large Language Model (LLM). It was functional but behaved like a generic chatbot.


## Making the Study Assistant Smarter

Right now, our assistant just passes a question to the LLM. It works, but it behaves like a generic chatbot, Let's set overall behavior, guidelines, and context for the AI so that it will break down the concepts and explain in clear and understandable way


### To make our Study Assistant smart:

1.  **Add Personality**: Make the assistant respond in a specific style (e.g., Friendly, Academic).
2.  **Set Overall Behaviour**: Define clear instructions for how the assistant should act.
3.  **Control the Output**: Manage the length and creativity of the generated text.

The overall flow for our enhanced assistant will be:

**Input** → **Prompt Construction** → **Model Call** → **Output**


## Understanding Chat Model Roles

When you interact with a conversational LLM, the conversation is structured using three distinct roles: **System**, **User**, and **Assistant**. Understanding this structure is key to guiding the AI's behavior.

-   **System**: These are the background instructions you give the AI before the conversation starts. It sets the overall behavior, tone, personality, and rules. Think of it as telling the AI, ""Hey, behave like a professional coach"" or ""Explain this concept to a complete beginner.""

-   **User**: This is your actual input, the question or task you provide to the AI.

-   **Assistant**: This is the AI's response based on your instructions and the preceding conversation. The history of assistant responses provides context for follow-up interactions.

The **System Prompt** is the most powerful tool for guiding the AI’s behavior before you even ask your question.


## Implementing System Prompts

A **System Prompt** is a short instruction that tells the LLM how to behave before it answers anything. It sets the tone, personality, and rules for the assistant.

<details>
<summary><strong>Python code for updating prompt of the Study Assistant</strong></summary>

```python
from google import genai
from google.colab import userdata

client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))

def study_assistant(question):
  prompt = f""You are my smart Study Assistant. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding. Here is my question: {question}""
  response = client.models.generate_content(
    model=""gemini-2.5-flash"",
    contents=prompt
  )
  return response.text
```

</details>


## Adding Personalities through System Prompts

We can make our assistant more dynamic by defining multiple personalities and letting the user choose one. A Python dictionary is a great way to store these predefined personalities. The `GenerateContentConfig` object is the mechanism through which we pass the selected system instruction (personality) to the Gemini model.

<details>
<summary><strong>Python code for defining and using personalities</strong></summary>

We'll create a dictionary where each key is a personality name and the value is the corresponding system prompt.

```python
personalities = {
  ""Friendly"": ""You are a friendly, enthusiastic, and highly encouraging Study Assistant. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding."",
  ""Academic"": ""You are a strictly academic, highly detailed, and professional university Professor. Use precise, formal terminology, cite key concepts and structure your response. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding.""
}
```

Next, we update our `study_assistant` function to accept a `persona` argument. This argument will be used as a key to retrieve the correct system prompt from our `personalities` dictionary.

```python
from google import genai
from google.colab import userdata
from google.genai import types

client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

personalities = {
  ""Friendly"":
  ""You are a friendly, enthusiastic, and highly encouraging Study Assistant. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding"",
  ""Academic"":
  ""You are a strictly academic, highly detailed, and professional university Professor. Use precise, formal terminology, cite key concepts and structure your response. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding""
}

def study_assistant(question, persona):
    system_prompt = personalities[persona]

    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
        contents=question
    )
    return response.text

question = ""What are LLMs?""
personality = ""Friendly""
print(study_assistant(question, personality))
```

</details>


## Controlling Generation Settings

Beyond personality, we can also control *how* the model generates its responses. The two most important settings for this are **temperature** and **maximum output tokens**.

### Temperature

**Temperature** controls the randomness of the model's output. Increasing the temperature value increases the randomness of the output. For Gemini, the range is typically from 0 to 2.

-   **Temperature = 0 (Deterministic)**: The model becomes very focused and consistent. The same input will almost always produce the same output. Best for factual answers, code generation, or math.
-   **Temperature = 0.7 (Balanced)**: A good mix of consistency and creativity. It produces some variation in responses, making it ideal for most general applications.
-   **Temperature = 1.2+ (Creative)**: The model becomes very random and creative, leading to unexpected and varied responses. Best for creative writing, brainstorming, or storytelling.

### Max Tokens

**Tokens** are the chunks of text the model processes (e.g., words, parts of words). We can set `max_output_tokens` to control the length of the response.

Just as there's a limit to the output length, there's also a maximum limit to the length of the input prompt, sometimes referred to as `max_input_tokens`. This limit is crucial to avoid errors and varies depending on the specific model used.

Why control tokens?

- **Control costs**: You pay per token (both input and output).
- **Keep responses concise**: Prevent overly long answers.

**Typical Ranges:**

-   **50-100 tokens**: A short answer (one paragraph).
-   **500-1000 tokens**: A medium response (a few paragraphs).
-   **2000+ tokens**: A long response (essay-length).

<details>
<summary><strong>Final python code</strong></summary>

We can add `temperature` and `max_output_tokens` to the same `GenerateContentConfig` object where we defined our system prompt.

```python
from google import genai
from google.colab import userdata
from google.genai import types

client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

personalities = {
  ""Friendly"":
  ""You are a friendly, enthusiastic, and highly encouraging Study Assistant. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding"",
  ""Academic"":
  ""You are a strictly academic, highly detailed, and professional university Professor. Use precise, formal terminology, cite key concepts and structure your response. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding""
}

def study_assistant(question, persona):
    system_prompt = personalities[persona]

    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=1000
        ),
        contents=question
    )
    return response.text

question = ""What are LLMs?""
personality = ""Friendly""
print(study_assistant(question, personality))
```
</details>


## Rate Limits and Costs

When working with APIs, there are practical limitations to keep in mind:

-   **Rate Limits**: This defines how many requests per minute your app can send (e.g., 60 requests/minute). Exceeding this limit will result in a `RateLimitExceededError`.
-   **Token Allowances**: Free tiers often have caps on the number of tokens you can use per day or per month. Remember that ""tokens"" includes both your input prompt and the model's output. Large inputs will consume your allowance faster.


## ServerError
Occasionally, you might encounter a `ServerError` when interacting with the Gemini API. This typically indicates an issue on the server-side, such as the Gemini service being temporarily unavailable, undergoing maintenance, or experiencing high traffic. In such cases, retry executing your code after sometime.

---

# Building UI for LLM Applications

In previous sessions, we focused on building LLM applications using Python, specifically making our Study Assistant smarter by utilizing **System Prompts** and **Generation Settings**. Now, we'll shift our focus to **Building User Interfaces for LLM Applications**.

## The Problem with Just Code

Currently, our code can only be run within a coding environment. This presents a challenge:

- What if we want to make our application more presentable and usable by others?

## The Solution: UI and Deployment

To make our LLM applications truly accessible and user-friendly, we need two key components:

1.  **A Simple UI**: To allow people to easily interact with the app.
2.  **Deployment**: So anyone can access it online without needing to run it locally.

## Understanding UI for Web Applications

When we think about the applications we use every day, they all started as code written by developers but were transformed into real applications through a User Interface (UI).

Traditionally, building a web application requires:

- Using HTML/CSS for the interface
- Using JavaScript for interactivity
- Setting up and managing servers
- Understanding web development frameworks

However, for AI/ML projects, there are tools specifically designed to simplify this process. These tools allow you to focus on your Python code while automatically handling the interface and hosting.

### UI-Building Approaches

There are several ways to turn Python code into a usable interface:

1.  **UI building frameworks (e.g., Gradio, Streamlit)**
2.  **Full code options (HTML/CSS/JS frameworks)**
3.  **No-code/low-code builders**

In this session, we will be using **Gradio** due to its efficiency in rapidly creating web applications from Python code.

## Introduction to Gradio

Gradio is an open-source Python library that simplifies the process of turning your code into a shareable web application. It allows you to create interactive AI demos, such as chatbots or image generators, without the need to build a full website using traditional web development technologies.

### What Gradio Offers

-   **Different input types**: Text boxes, sliders, dropdowns, chat windows, and even image or webcam inputs.
-   **Multiple output types**: Text, images, audio, plots.
-   **Automatic web interface generation**: No HTML/CSS needed, as Gradio handles it for you.
-   **Built-in sharing**: Can create temporary public links instantly.

### Understanding the Gradio Workflow

Gradio's primary role is to:

1.  Create a visual interface for your input (e.g., text boxes, buttons).
2.  Take what the user types/selects from the UI.
3.  Pass this input to your Python function.
4.  Display the result from your Python function in a user-friendly format.

Gradio manages the web components, handles data flow between the UI and your Python function, and displays results in real-time.

## Building UI for Study Assistant with Gradio

Let's integrate Gradio into our Study Assistant application step by step.

### Initial Python Code (from previous session)

Our **Study Assistant**, which answers questions with a chosen personality:

```python
from google import genai
from google.colab import userdata
from google.genai import types

client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

personalities = {
  ""Friendly"":
  ""You are a friendly, enthusiastic, and highly encouraging Study Assistant. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding"",
  ""Academic"":
  ""You are a strictly academic, highly detailed, and professional university Professor. Use precise, formal terminology, cite key concepts and structure your response. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding""
}

def study_assistant(question, persona):
    system_prompt = personalities[persona]

    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=2000
        ),
        contents=question
    )
    return response.text

question = ""What are LLMs?""
personality = ""Friendly""
print(study_assistant(question, personality))
```

### Installing Gradio

First, install the Gradio library in your environment:

```python
!pip install -q gradio
```
-   `!pip install -q gradio`: This command installs the Gradio Python library. The `!` tells the environment (like Colab) to execute a shell command, `pip` is the Python package installer, and `-q` means ""quiet"" installation, suppressing verbose output.

### Importing Gradio
```python
import gradio as gr
```
-   `import gradio as gr`: This imports the Gradio library and assigns it the alias `gr` for easier use in code.

### Creating the Gradio Interface

Gradio provides a special class called `Interface` to quickly create a demo for your Python function.

#### Syntax for `Interface()`

The `gr.Interface()` class takes several key parameters:

-   `fn`: The Python function that Gradio should run when the user interacts with the UI.
-   `inputs`: Defines how to take input for your function (e.g., `gr.Textbox`, `gr.Radio`).
-   `outputs`: Defines how to display the output from your function.
-   `title`: The title of your application, displayed at the top of the UI.
-   `description`: A short description shown below the title.

#### Input and Output Types in Gradio

Gradio offers a variety of components for inputs and outputs:

-   **Inputs**: `gr.Textbox`, `gr.Radio`, `gr.Dropdown`, `gr.Image`, `gr.Slider`, etc.
-   **Outputs**: `gr.Textbox`, `gr.Image`, `gr.JSON`, `gr.Audio`, `gr.Plot`, etc.

#### Full Gradio UI Code for Study Assistant

Now, let's put it all together to create the Gradio interface for our `study_assistant` function:

```python
import gradio as gr
from google import genai
from google.genai import types
from google.colab import userdata

client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))

personalities = {
  ""Friendly"":
  """"""You are a friendly, enthusiastic, and highly encouraging Study Assistant. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding"""""",
  ""Academic"":
  """"""You are a strictly academic, highly detailed, and professional university Professor. 
  Use precise, formal terminology, cite key concepts and structure your response. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding""""""
}

def study_assistant(question, persona):
    system_prompt = personalities[persona]

    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=2000
        ),
        contents=question
    )
    return response.text

demo = gr.Interface(
    fn=study_assistant,
    inputs=[
        gr.Textbox(lines=4, placeholder=""Ask a question..."", label=""Question""),
        gr.Radio(choices=list(personalities.keys()), value=""Friendly"", label=""Personality"")
    ],
    outputs=gr.Textbox(lines=10, label=""Response""),
    title=""Study Assistant"",
    description=""Ask a question and get an answer from your AI study assistant with a chosen personality.""
)

```
### Launching the App

To make your Gradio application run and be accessible:

```python
demo.launch(debug=True)
```
-   `demo.launch(debug=True)`: This command starts the Gradio web server. 
- `debug=True` provides additional debugging information in the console, which is useful during development.

### Final Code

```python
import gradio as gr
from google import genai
from google.genai import types
from google.colab import userdata

client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))

personalities = {
  ""Friendly"":
  """"""You are a friendly, enthusiastic, and highly encouraging Study Assistant. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding"""""",
  ""Academic"":
  """"""You are a strictly academic, highly detailed, and professional university Professor. 
  Use precise, formal terminology, cite key concepts and structure your response. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding""""""
}

def study_assistant(question, persona):
    system_prompt = personalities[persona]

    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=2000
        ),
        contents=question
    )
    return response.text

demo = gr.Interface(
    fn=study_assistant,
    inputs=[
        gr.Textbox(lines=4, placeholder=""Ask a question..."", label=""Question""),
        gr.Radio(choices=list(personalities.keys()), value=""Friendly"", label=""Personality"")
    ],
    outputs=gr.Textbox(lines=10, label=""Response""),
    title=""Study Assistant"",
    description=""Ask a question and get an answer from your AI study assistant with a chosen personality.""
)

demo.launch(debug=True)
```

---

# Deploying LLM Applications

In the previous sessions, we've built powerful LLM applications that run in our local environments like Google Colab. Now, it's time to take the final step: deploying our application to make it accessible to anyone in the world.

This unit will guide you through the process of deploying an LLM application using Hugging Face Spaces, transforming your code into a fully functional web app.

# Understanding Deployment

Right now, our Study Assistant application exists only within our Google Colab. This means only we can run it, and it's only active while our Colab notebook is running.

**Deployment is the process of moving our application from our local environment to a publicly accessible server on the internet.**

We will use **Hugging Face Spaces** to serve our application.

## What are Hugging Face Spaces?

Hugging Face Spaces is a free hosting service provided by Hugging Face, specifically designed for showcasing AI and machine learning applications.

### How It Works

The process is straightforward:

1.  **Upload Files**: We upload our application code (`app.py`) and a list of dependencies (`requirements.txt`).
2.  **Add Secret Keys**: We securely add our API keys (like the Gemini API key) without exposing them in our code.
3.  **Automatic Deployment**: Hugging Face automatically builds and deploys our application on the cloud.
4.  **Get a Live URL**: We receive a permanent, public URL that we can share with anyone. The app stays online 24/7 (with some limitations).


# Preparing for Permanent Deployment

When we use `demo.launch()` in Gradio, it creates a temporary, shareable link that only works while our Colab notebook is active. For permanent deployment, we need to package our code into files that can run independently on a server.

We'll need two main files:
1.  `app.py`: Contains our application's Python code.
2.  `requirements.txt`: Lists all the Python libraries our app needs to run.

### Code Modifications for Deployment

Before we can deploy, we need to make two simple but crucial modifications to our Study Assistant code.

<details>
<summary><strong>First Modification: Create `app.py` File</strong></summary>

To package our code into a file, we can use a ""magic command"" in our Colab notebook. By adding `%%writefile app.py` at the very top of the cell containing our application code, we instruct Colab to save the entire cell's content into a file named `app.py`.

```python
%%writefile app.py
import gradio as gr
from google import genai
from google.genai import types
from google.colab import userdata

client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))

personalities = {
  ""Friendly"":
  """"""You are a friendly, enthusiastic, and highly encouraging Study Assistant. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding"""""",
  ""Academic"":
  """"""You are a strictly academic, highly detailed, and professional university Professor. 
  Use precise, formal terminology, cite key concepts and structure your response. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding""""""
}

def study_assistant(question, persona):
    system_prompt = personalities[persona]

    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=2000
        ),
        contents=question
    )
    return response.text

demo = gr.Interface(
    fn=study_assistant,
    inputs=[
        gr.Textbox(lines=4, placeholder=""Ask a question..."", label=""Question""),
        gr.Radio(choices=list(personalities.keys()), value=""Friendly"", label=""Personality"")
    ],
    outputs=gr.Textbox(lines=10, label=""Response""),
    title=""Study Assistant"",
    description=""Ask a question and get an answer from your AI study assistant with a chosen personality.""
)

demo.launch(debug=True)
```
</details>

<details>
<summary><strong>Second Modification: Access API Key from Environment Variables</strong></summary>

Our current code gets the API key from Colab's secrets manager, which won't be available in Hugging Face. We need to modify it to read the key from the server's ""environment variables"" (which Hugging Face calls ""Secrets"").

1.  **Remove Colab-specific import**: We no longer need to import `userdata` from `google.colab`.
2.  **Add `os` import**: We'll use Python's built-in `os` library to access environment variables.
3.  **Update genai.Client**: We'll change how the client is initialized to use `os.getenv()`.

**From this:**

```python
from google.colab import userdata
client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))
```

**To this:**

```python
import os
client = genai.Client(api_key=os.getenv(""GEMINI_API_KEY""))
```
This tells our app to look for a secret named `GEMINI_API_KEY` in the Hugging Face environment.

#### **Final `app.py` Code Structure**
```python
%%writefile app.py
import gradio as gr
from google import genai
from google.genai import types
import os

client = genai.Client(api_key=os.getenv(""GEMINI_API_KEY""))

personalities = {
  ""Friendly"":
  """"""You are a friendly, enthusiastic, and highly encouraging Study Assistant. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding"""""",
  ""Academic"":
  """"""You are a strictly academic, highly detailed, and professional university Professor. 
  Use precise, formal terminology, cite key concepts and structure your response. 
  Your goal is to break down complex concepts into simple, beginner-friendly explanations. 
  Use analogies and real-world examples that beginners can relate to. 
  Always ask a follow-up question to check understanding""""""
}

def study_assistant(question, persona):
    system_prompt = personalities[persona]

    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=2000
        ),
        contents=question
    )
    return response.text

demo = gr.Interface(
    fn=study_assistant,
    inputs=[
        gr.Textbox(lines=4, placeholder=""Ask a question..."", label=""Question""),
        gr.Radio(choices=list(personalities.keys()), value=""Friendly"", label=""Personality"")
    ],
    outputs=gr.Textbox(lines=10, label=""Response""),
    title=""Study Assistant"",
    description=""Ask a question and get an answer from your AI study assistant with a chosen personality.""
)

demo.launch(debug=True)
```
</details>

<details>
<summary><strong>Creating the `requirements.txt` File</strong></summary>

Next, we need to tell Hugging Face which Python libraries to install. We do this by creating a `requirements.txt` file.

In a new cell in your Colab notebook, use the `%%writefile` command again:

```python
%%writefile requirements.txt
gradio
google-genai
```
This file lists the `gradio` and `google-genai` packages, which Hugging Face will automatically install before running our app.

<MultiLineWarning text=""Important"">
After running both `%%writefile` cells, you must download the newly created `app.py` and `requirements.txt` files from the Colab file browser. You will need them for the next steps.
</MultiLineWarning>

</details>


# Step-by-Step Deployment Process

Now that we have our files ready, let's deploy our app to Hugging Face Spaces.

<details>
<summary><strong>Step 1: Create a Hugging Face Account</strong></summary>

-   Go to <a href=""https://huggingface.co"" target=""_blank"">huggingface.co</a>
-   Click **""Sign Up""** in the top right.
-   Create a free account. You can sign up with Google or GitHub for a faster process.
</details>

<details>
<summary><strong>Step 2: Create a New Space</strong></summary>

-   Once logged in, click your profile icon (top right) and select **""New Space""**.
-   Configure your Space with the following settings:
    -   **Space name**: Choose a unique name for your app (e.g., `my-study-assistant`).
    -   **License**: `MIT`
    -   **Space SDK**: `Gradio`
    -   **Template**: `Blank`
    -   **Hardware**: `CPU basic` (this is free and sufficient).
    -   **Visibility**: `Public`
-   Click **""Create Space""**.
</details>

<details>
<summary><strong>Step 3: Add Your API Key as a Secret</strong></summary>

This is a critical step for security. We must never paste our API key directly into our code.

-   In your new Space, click the **""Settings""** tab.
-   Scroll down to the **""Variables and secrets""** section.
-   Click **""New secret""**.
-   Fill in the details:
    -   **Name**: `GEMINI_API_KEY` (This must match exactly what's in `os.getenv(""GEMINI_API_KEY"")`).
    -   **Secret value**: Paste your actual Gemini API key here.
-   Click **""Save secret""**.

Now your app can securely access the key without exposing it to the public.
</details>

<details>
<summary><strong>Step 4: Upload Your Files</strong></summary>

-   Go to the **""Files""** tab in your Space.
-   Click the **""Contribute""** button and select **""Upload files""**.
-   Drag and drop (or select) both your `app.py` and `requirements.txt` files.
-   Add a commit message (e.g., ""Initial commit"").
-   Click **""Commit changes to main""**.
</details>

<details>
<summary><strong>Step 5: Wait for the Build and Test Your App!</strong></summary>

Once you commit the files, Hugging Face automatically starts the build process. You will see a ""Building"" status. This might take 1-2 minutes.

-   Hugging Face creates a Python environment.
-   It installs the packages from `requirements.txt`.
-   It runs your `app.py` file.

Once complete, your Gradio application will appear directly on the page! You can now interact with it live.

### Share Your Link

Your app is now live at a permanent URL. You can find it in your browser's address bar. The format will be:
`https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

You can share this link with friends, add it to your portfolio, or include it in your resume!
</details>


# Understanding Free Space Limitations

Hugging Face's free tier is fantastic for student projects and demos, but it has some limitations:

<details>
<summary><strong>Sleep Mode</strong></summary>
If your app is inactive for about 48 hours, it will ""sleep"" to conserve resources. The first person to visit it after it sleeps will experience a short loading time (around 20 seconds) as the app wakes up.
</details>

<details>
<summary><strong>Performance</strong></summary>
The free tier has limited CPU and RAM. If your app gets a lot of traffic at once, it may slow down.
</details>

<details>
<summary><strong>Storage</strong></summary>
There is limited storage space, so it's not suitable for applications that need to store very large files.
</details>


---

# Understanding How LLMs Work | Part 1

## Introduction

In previous sessions, you've built and deployed your own LLM-powered applications. Until now, Large Language Models (LLMs) have been treated as a ""black box"" where input goes in, ""magic happens,"" and a response comes out. This session aims to open that box and explore the underlying mechanisms.

---

## What is an LLM?

A Large Language Model (LLM) is an advanced type of AI model trained on vast amounts of text data to process, understand, and generate human language.

### Key Characteristics:

*   **Training:** Learns patterns from petabytes of datasets (books, Wikipedia, billions of websites).
*   **Resources:** Requires millions of CPU/GPU/TPU resources, terabytes of memory, months of training time, and significant cost.
*   **Development:** Involves top-notch researchers, developers, and entrepreneurs.
*   **Parameters:** Composed of billions of parameters (weights and architecture). A higher number of parameters generally leads to more efficient and higher-quality outcomes.
*   **Language:** Processes and generates text data in various languages.

### Capabilities:

LLMs possess diverse capabilities, including:

*   Reasoning
*   Language Understanding
*   Summarization
*   Text Generation
*   Language Translation

---

## How LLMs Work: Next-Word Prediction

At its core, an LLM operates on the principle of next-word prediction, similar to how humans complete familiar sentences.

### Activity: Predict the Next Word

Consider these sentences:

*   ""Honesty is the best \_\_\_\_\_\_""
*   ""Twinkle twinkle little \_\_\_\_\_\_""

Most people can immediately predict the next word because they have seen these patterns previously. LLMs do the same, but on a much larger scale, having processed billions of sentences and understood countless patterns.

### Next-Word Prediction in Action:

Imagine the LLM processing a sentence like ""A quick brown fox jumps..."":

*   **Input:** ""A quick brown fox jumps""
*   **LLM Predicts:** ""over""
*   **Input:** ""A quick brown fox jumps over""
*   **LLM Predicts:** ""the""
*   **Input:** ""A quick brown fox jumps over the""
*   **LLM Predicts:** ""lazy""
*   **Input:** ""A quick brown fox jumps over the lazy""
*   **LLM Predicts:** ""dog""
*   **Input:** ""A quick brown fox jumps over the lazy dog""
*   **LLM Predicts:** ""STOPS"" (End of sentence)

This iterative process of predicting the most probable next word allows LLMs to generate coherent and contextually relevant text.

---

## Transformer Architecture: The Foundation of Modern LLMs

Historically, various architectures like Recurrent Neural Networks (RNNs) and Long Short-Term Memory (LSTMs) were used to handle text data. However, the **Transformer architecture**, introduced by Google in 2017 in the paper **Attention Is All You Need**, revolutionized the field of Generative AI. Most modern LLMs, including GPT (Generative Pre-trained Transformer), are built upon this architecture.

### The Memory Fading Problem

Earlier architectures like RNNs and LSTMs processed text sequentially, one word at a time. This led to a significant problem: **memory fading**. In long sentences, the model would often ""forget"" earlier words by the time it reached the end, making it difficult to understand long-range dependencies.

**Example of Memory Fading:**

```

The movie that my friend told me to watch last week, which had the funny superhero fighting aliens,
it was actually...

```

By the time the model reached ""it was actually..."", older models struggled to remember what ""it"" referred to (the movie).

Transformers solve this by looking at the **entire sentence at once**, not word-by-word. This parallel processing allows them to:

*   Understand relationships in long sentences (e.g., ""movie"" connects to ""amazing"").
*   Retain information from earlier words.
*   Train and generate much faster.

---


## Pre-processing Steps: Preparing Text for the LLM

LLMs don't directly understand text, they operate on numbers. Therefore, input text must be converted into a numerical format through a series of pre-processing steps:

1.  **Tokenization**
2.  **Embedding**
3.  **Positional Encoding**

### 1. Tokenization: Breaking Text into Chunks

**Tokenization** is the process of splitting a sentence into smaller parts called **tokens**. Tokens can be:

*   Entire words (e.g., ""I"", ""love"", ""Tennis"")
*   Parts of words (subwords, e.g., ""Play"" + ""ing"" for ""Playing"")
*   Even single characters (e.g., ""?"")

Think about how you remember a long phone number like ""6640230120"". Most people break it into smaller, easier-to-remember chunks (e.g., ""66 402 301 20""). Similarly, LLMs break text into tokens for easier processing and pattern recognition.

A single word can sometimes be broken into multiple tokens.

**Example:**

*   ""I love Tennis."" → ""I"", ""love"", ""Tennis"", "".""
*   ""Playing"" → ""Play"", ""ing""

<details>
<summary><strong>Visualizing Tokenization</strong></summary>

You can explore how different models tokenize text using tools like the <a href=""https://platform.openai.com/tokenizer"" target=""_blank"">OpenAI Tokenizer</a>. 
</details>
<MultiLineNote>Note that different models use different tokenizers and techniques.
</MultiLineNote>
### 2. Embeddings: Converting Tokens to Numbers

After tokenization, each token is converted into a list of numbers called a **vector**. This numerical representation is known as an **embedding**.

*  Embeddings capture the meaning of a token in a numeric form. They are not random numbers.
*  Embeddings place words in a multi-dimensional space where similar relationships point in the same direction (e.g., the vector difference between ""King"" and ""Queen"" might be similar to ""Man"" and ""Woman""). This allows the model to understand relationships between words.

<details>
<summary><strong>Visualizing Embeddings</strong></summary>

Tools like the <a href=""https://projector.tensorflow.org/"" target=""_blank"">TensorFlow Projector</a>. can help visualize word embeddings in a 2D or 3D space.
</details>

### 3. Positional Encoding: Adding Order to Parallel Processing

Since Transformers process the entire input simultaneously, it is important to understand the order of words in a sentence. This is where **positional encoding** comes in.

* Positional data is added to each embedding, informing the model about the word's position within the sentence.
* Without positional encodings, a Transformer would consider sentences like ""The dog chased the ball"" and ""The ball chased the dog"" to be identical, as it would only see the collection of words, not their sequence.

**Example:**
Input sentences:

*   “The dog chased the ball”
*   “The ball chased the dog”

Both sentences contain the same words, but the order of the words is different, which changes the meaning.Positional encodings, helps the Transformer to understand both the sentences are different.

---

## High-Level Transformer Architecture: Encoder and Decoder in Action

After pre-processing, the numerical representations (embeddings with positional encoding) are fed into the Transformer's core components:

*   **Encoders:** The encoder is responsible for reading and processing these contextual embeddings. It helps in understanding the meaning and the intent behind the input.
*   **Decoders:** The decoder uses the encoder's understanding to decide what token should be generated next, producing the output sequentially.

This encoder-decoder flow is what allows LLMs to both understand and generate language effectively.

---

# Understanding How LLMs Work | Part 2

## Introduction

In Part 1, we explored the foundational concepts of Large Language Models (LLMs), including their core function of next-word prediction, the necessity of the Transformer architecture, and the initial pre-processing steps (Tokenization, Embedding, and Positional Encoding). Now lets understand the internal workings of the Transformer's Encoder and Decoder components.

---

## Transformer Architecture: The Encoder

As discussed, the **Encoder** is responsible for reading and processing the input embeddings to understand the meaning and intent behind the text. Each encoder layer consists of several sub-layers:

1.  **Multi-Head Attention**
2.  **Add & Norm **
3.  **Feed-Forward Network**

### 1. Multi-Head Attention

Multi-Head Attention is crucial for capturing diverse relationships (syntactic, semantic, emotional) within the input sentence. It achieves this through multiple ""heads,"" each focusing on a slightly different aspect of the relationships between words.

*   **Self-Attention:** The core mechanism within Multi-Head Attention is **Self-Attention**. For each word in a sentence, Self-Attention computes how much focus that word should give to every other word in the same sentence to understand its context.

    **Example:** In ""She saw a bat.""
    *   If the surrounding text is about cricket, ""bat"" will be strongly associated with a cricket bat.
    *   If the text is about nocturnal animals, ""bat"" will be strongly associated with the animal.

    This mechanism allows the model to capture complex relationships and disambiguate word meanings based on context.

### 2. Add & Norm

This sub-layer performs two critical functions:

*   **Add :** Adding outputs from multiple heads along with input to preserve 
original information. 
*   **Norm(Noramalizaton) :** Maintains the numbers within working range of [-1, 1]. 
Sets mean = 0 and standard deviation = 1

### 3. Feed-Forward Network (FFN)

* Further mix and transform the processed information from the attention layer.
* Expand the representation to capture richer and better features. 

    ** Example:** 
    
    - The word ""bat"" might be expanded into features like ""cricket, game, sport"" or ""mammal, wings, night"" depending on the context.

These layers are typically stacked multiple times to create a encoder. The final output of the encoder is a set of **contextual embeddings**, which represent each token's meaning shaped by its surrounding tokens.

---

## Transformer Architecture: The Decoder

The **Decoder** is responsible for generating the output sequence, one token at a time, based on the encoder's understanding and the previously generated tokens. Each decoder layer also has several sub-layers:

1.  **Masked Multi-Head Attention (Self-Attention)**
2.  **Multi-Head Attention (Cross-Attention)**
3.  **Add & Norm**
4.  **Feed-Forward Network (FFN)**

### 1. Masked Multi-Head Attention (Self-Attention)

This is similar to the encoder's Multi-Head Attention but with a crucial difference: **masking**.

During training, the decoder is prevented from ""looking ahead"" at future tokens in the target sequence. It can only attend to the words that have already been generated.

### 2. Multi-Head Attention (Cross-Attention)

This attention mechanism allows the decoder to focus on relevant parts of the **encoder's output** (the contextual embeddings). It asks, ""What's most important from the input right now?"" and gets fresh answers from the encoder for each token it generates.


### 3. Feed Forward Neural Network and Add & Norm

These layers function similarly to their counterparts in the encoder, transforming and normalizing the information to produce richer features and prevent context loss. However, the specific transformations learned will be different due to their role in generation rather than just understanding.

---

## How LLMs Work: Flow Overview

In summary, the process of an LLM generating a response involves four main steps:

1.  **Input Processing:** The input text is tokenized, embedded, and positional encodings are added.
2.  **Encoder Captures Context:** The encoder processes these numerical inputs, using Multi-Head Attention, Add & Norm, and FFNs to build a rich contextual understanding.
3.  **Decoder Generates Output:** The decoder uses Masked Multi-Head Attention (for self-attention), Cross-Attention (to interact with the encoder's output), Add & Norm, and FFNs to generate output embeddings sequentially.
4.  **Converting Output to Natural Language:** The Linear and Softmax layers convert the decoder's output embeddings into actual words, predicting the most probable next token until the response is complete.

---

## Future Trends in LLMs

The field of LLMs is rapidly evolving, with key trends including:

*   **Larger Contexts:** Continued expansion to multi-million token windows for processing entire books, videos, and vast datasets.
*   **Enhanced Reasoning:** Development of models that prioritize step-by-step thinking and more robust logical capabilities.
*   **Multimodality:** Seamless integration of various data types like text, images, audio, and video (e.g., Google Gemini).
*   **Ethics:** Ongoing focus on developing better safeguards against biases, hallucinations, and other ethical concerns.

Staying updated with these advancements is essential as LLMs continue to reshape technology and applications.

---

#Introduction
****In this session, lets explore several AI tools and platforms, including **Claude skills**, **Gemini guided learning**, **Google Antigravity**, **Comet browser**, and other **AI tools discovery platforms**.

---

### Google Anti-gravity

Google Antigravity is an agent-first coding workspace by Google, powered by latest Gemini models, where agents can use the editor, terminal, and browser to work and collaborate via a central manager view.

** Key Features **

**1. Works on its own**

Antigravity doesn’t just give code suggestions. Its agents can **plan, write, run, test, and fix code by themselves**.

**2. Team of agents**

Antigravity can involve **multiple agents working** simultaneously.

**3. Can use all tools**

It can control the **editor, terminal, and browser** to do real work, not just show code.

**4. Brilliant model**

Built on latest Gemini models, it can think, plan, and handle tricky tasks better than other assistants.

## **How to use**

- Visit <a href=""https://antigravity.google/"" target=""_blank"">https://antigravity.google/</a> and then Download it
- Launch it on your system and choose a model
- You give Antigravity a **project idea or prompt**
- It **plans the steps** automatically and assigns tasks to agents
- Agents **write code, run tests, and verify results**
- You can **review feedback** and the agents refine their work


<details>
<summary>**Example**</summary>

**Project:** Build a webpage showing local time with background changing for day/night.

**Prompt:**

```
Create a simple webpage that shows the current local time and automatically changes the background color to light during the day and dark at night.After coding, run it in the browser, verify it works, and provide a screenshot and a short report of what you did.
```
    
</details>

---


###Gemini Guided Learning

**Gemini Guided Learning** is an AI-powered tutor that helps you learn topics step by step. You can ask questions, practice exercises, get hints, and it uses colorful visuals to make learning engaging.

**How to Start:**

- Go to <a href=""https://gemini.google.com/"" target=""_blank"">Google Gemini</a>
- Click on Tools
- Then click on **Guided Learning**




## **How It Works**
1. Choose a topic (Algebra, History, Python…)
2. AI explains each step and asks questions
3. Practice exercises and get feedback
4. Receive hints if you get stuck
5. Complete the topic at your own pace

<details>
<summary>**Example Prompts**</summary>

```
Explain how Large Language Models (LLMs) work step by step with animations, practical examples, and quizzes.


```

```
Teach me Python loops step-by-step (for, while, nested loops). Include simple visuals or diagrams, short explanations of how each loop works.

```
</details>

## **Why It’s Helpful**

- Breaks topics into **easy steps**
- Provides **personalized guidance**
- Helps **practice actively**
- Gives **instant hints and feedback**

---

 ###Claude Skills

Before we explore Claude Skills, it helps to understand Claude itself.

Claude is an AI assistant created by Anthropic, designed to help with tasks, projects, and coding.

** What We Had Before **

- **General Instructions**: Save preferred behavior and tone.

- **Claude Projects**: Keep files, notes, and chats organized.

- **Claude Code**: Explain code, suggest fixes, and generate snippets.

**Claude Skills**

Claude Skills are smart, reusable shortcuts that let Claude perform tasks automatically. Once you set up the instructions, Claude can execute the whole task with a simple command — no need to repeat anything again.



**What Claude Skills Are Designed For**

- **Standard & Consistent Output**: They follow the same rules and format every time, ensuring clean and accurate results.

- **Specialized Expert Tasks**: They apply expert-level knowledge to handle complex tasks quickly and smoothly.


<details><summary>**How to Use Existing Claude Skills**</summary>

### **Enable existing skills**

- Go to **Settings → Capabilities**
- Scroll to the **Skills** section
- You will see many **built-in skills**
- **Toggle ON** any skill you want to use

### **How to trigger a skill**

- Come back to the main **Chat**
- Just ask Claude to perform a task
- Claude automatically detects and triggers the correct skill

- **Example:**
    
    ```
    Create a poster for the AI Workshop with modern layout and icons
    
    ```
    
    - Auto uses the Canvas-Design skill
    
</details>


<details><summary> **How to Create New Claude Skills**</summary>

### **1.Enable Skill Creation**

- Go to **Settings → Capabilities**
- In **Skills** section → **toggle ON: Skill-Creator**
- Go to **Chat**
- Prompt Claude:

```
Create a new skill

```

### **2.Claude opens the Skill Creator guide and follow the Guide**

### **3.Output**

- Claude generates a **ZIP file** containing:
    - Reference files
    - README
    - `SKILL.md` files



## **4.Upload the New Skill**

- Go to **Settings → Capabilities → Skills**
- Click **Upload Skill**
- Select the ZIP file
- Skill becomes available in your Skill list



## **5.Use Your New Skill**
**Example:**

```
Use the Revision Sheet skill to turn all PDFs into a quick revision document
```

</details>

---

### Comet AI Browser

Comet is an AI-powered web browser by **Perplexity AI** (2025) it is built on **Chromium** with AI tools inside the browser.

** How to use**

- **Download & Install** from <a href=""https://perplexity.ai/comet"" target=""_blank"">perplexity.ai/comet</a>
- **Import Bookmarks & Extensions** from Chrome for continuity
- **Set as Default** (optional)
  - Go to Settings → Default Browser
- **Use Prompts** in the side chat panel to automate tasks


# **How Comet is Different from Other Browsers**
- Open Google Maps and use the prompt given below.

**Prompt:**

```
Find a cafe within 5 km with rating above 4, outdoor seating, and check it on Street View

```

### **Comparision of Results between Comet and Google Chrome**

**Comet AI Browser**

- Shows summary + comparisons automatically
- Gives details without clicking around

**Google Chrome**

- Shows separate results
- You need to check & compare manually

# **What Comet AI Browser Can Do**
1. Find and summarize info from websites
- Manage meetings and emails automatically
- Keep your tabs neat and show important points
- Help you shop better by comparing products and prices

---


### AI Tools Discovery Platforms

 **ThereIsAnAIForthat.com **

ThereIsAnAIForthat.com is a directory of thousands of AI tools. You can search by use case, such as writing, design, or productivity, to quickly find the right AI tool for your needs.

**Key Features & Benefits**

- **Browse & Search:** Explore tools by category or keywords
- **Filter Tools:** narrow choices efficiently
- **Compare Tools:**  choose the best fit
- **View Details:** Ratings, description, direct link
- **Discover New Tools:** Stay updated with latest AI innovations

**How to Use**

1. Open <a href=""https://theresanaiforthat.com/"" target=""https://theresanaiforthat.com/"">thereisanaiforthat.com</a>
2. Browse or search by category/use case
3. Apply filters as needed
4. Click a tool → view description, rating, link
5. Select & try the tool


---


# Tool Use & Function Calling in LLMs

## Introduction

So far, we have explored how to build applications that provide answers based on a Large Language Model's existing knowledge. But what happens when we need our application to access real-time data or interact with external systems? This session introduces **Tool Use**, also known as **Function Calling**, a powerful feature that allows LLMs to connect with external resources to perform tasks and retrieve dynamic information.

---

## The Problem: LLM Knowledge Limitations

LLMs are trained on vast datasets, but this knowledge is static and has a ""knowledge cutoff"" date. They do not have access to any information or events that occurred after their training was completed.

If you ask an LLM for current, real-time information without access to external tools, it cannot provide an accurate answer.

<details>
<summary><strong>Example: Asking for Current Information</strong></summary>

Let's ask a model for the latest iPhone, instructing it not to use a web search.

```
""Can you recommend the latest iPhone model (do not use web search)?""
```

Models like GPT, Gemini, and Claude will likely provide information about models that were the latest at the time their training data was collected, not the actual latest model available today.

</details>

This limitation prevents us from building applications that require real-time data, such as:

-   Current weather conditions
-   Live stock prices
-   Latest news headlines
-   Real-time sports scores
-   Today's calendar events

The solution to this is **Tool Calling**.

---

## What is Tool/Function Calling?
**Tool calling** (function calling) is a  powerful feature that allows LLMs to interact with external resources

This is different from how we used tools in a no-code platform like n8n. In n8n, the platform itself

- Manages tool connections. 
- Formats tool inputs / outputs
- Coordinates between LLM and tools

Now let us understand how we can integrate tools to LLMs in Python

---

## Let's Build: A Real-Time Weather Application

To understand how function calling works in practice, we will build a Python application that can provide the current weather for any city.

### Initial Code

we will be using the the following code to make calls to LLMs.



```bash
!pip install groq
```

```python
from google.colab import userdata
from groq import Groq

client = Groq(
  api_key=userdata.get('GROQ_API_KEY')
)

response = client.chat.completions.create(
  messages=[ {
    ""role"": ""user"",
    ""content"": ""What is the current weather in hyderabad"",
  }], model=""llama-3.3-70b-versatile"",
)
print(response.choices[0].message.content)
```



### Prerequisites

-   A **<a href=""https://console.groq.com/keys"" target=""_blank"">Groq API Key</a>** to access LLMs.
-   An **<a href=""https://home.openweathermap.org/api_keys"" target=""_blank"">OpenWeatherMap API Key</a>** to get real-time weather data.
- The URL Endpoint:

    ```
    http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}
    ```

<MultiLineNote>
Your OpenWeather API key will be activated automatically within 2 hours upon successful registration
</MultiLineNote>
-   Python environment with the `groq` and `requests` packages installed.

### Platform Support for Function Calling


Many LLM platforms now provide support for function calling, allowing their models to interact with external tools:

-   **OpenAI**: GPT models (e.g., `gpt-5`)
-   **Claude**: Anthropic's models (e.g., `claude-opus-4.5`)
-   **Gemini**: Google's models (e.g., `gemini-3-pro-preview`)
-   **Cohere**: Cohere's models (e.g., `command-a-03-2025`)
-   **Groq**: Supports various models, including Llama (e.g., `llama-3.3-70b-versatile`)
-   **Mistral AI**: Mistral's models (e.g., `mistral-large-latest`)

Let us use **Groq** for our weather application:

-   Groq is a platform that provides multiple AI models, including llama models.
-  Groq enables function calling by accepting a list of functions(tools) and returning structured JSON arguments from supported models

## Step 1: Create the Weather Function

First, we need a Python function that can fetch weather data from the OpenWeatherMap API. We'll use the `requests` library to make the API call.

<details>
<summary><strong>Code to Get Weather Information</strong></summary>

This function takes a `location`, calls the weather API, and returns a simplified dictionary with the key weather details.

```python
import json
import requests
from google.colab import userdata

def get_weather(location):
  api_key = userdata.get('WEATHER_API_KEY')
  url = f""http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}""

  response = requests.get(url)
  data = response.json()
  if data.get(""cod"") == 200:
    return json.dumps({
      ""location"": location,
      ""temperature"": data[""main""][""temp""],
      ""description"": data[""weather""][0][""description""]
    })
  else:
    return json.dumps({""Oops! Something went wrong.""})

# Example usage:
# print(get_weather(""Hyderabad""))
```

</details>

<MultiLineNote>
This `get_weather` function is just one example. You can replace it with any functionality you need - sending emails, calculations, or calling any other external API.
</MultiLineNote>

## Step 2: Define the Tool for the LLM

### What is a Tool?

A tool is a piece of functionality that we explicitly tell the model it has access to.When generating a response, the model decides whether it needs information from a tool to complete the task.

### Understanding Tools: Functionality We Give the Model

<img src=""https://s3.ap-south-1.amazonaws.com/new-assets.ccbp.in/frontend/loading-data/niat-course-projects/Copy%20of%20Tool%20Use%20%26%20Function%20Calling%20in%20LLMs%20%281%29.png"" alt="""">


This flow ensures that tools are used only when required, and simple questions are answered directly without unnecessary external calls.

<MultiLineNote>
**Important:** The LLM does not execute the tool — it only decides which tool to use and with what inputs.
</MultiLineNote>

### Examples of Tools

Tools can represent many kinds of real-world functionality:

-   Get current weather for a location
-   Send emails
-   Update spreadsheets
-   Schedule calendar events
-   Search the web

Each of these tools gives the LLM capabilities beyond its training data.

### Defining a Tool for an LLM

To describe a function in a format that an LLM understands, we use a JSON schema structure.

This schema contains:

-   Function metadata
-   Parameter specifications

### Tool Definition Structure

A tool definition consists of the following key fields:

| Field       | Purpose                               |
| :---------- | :------------------------------------ |
| `name`        | Function name the LLM will call       |
| `description` | What the function does                |
| `parameters`  | What inputs the function needs        |
| `properties`  | Details about each parameter          |
| `required`    | Which parameters are mandatory        |

### Tool Definition for get_weather function
<details>
<summary><strong>Code</strong></summary>

```python
tools = [
  {
    ""type"": ""function"",
    ""function"": {
      ""name"": ""get_weather"",
      ""description"": ""Get current weather for a city"",
      ""parameters"": {
        ""type"": ""object"",
        ""properties"": {
          ""location"": {
            ""type"": ""string"",
            ""description"": ""City name like Mumbai, London""
          }},
        ""required"": [""location""]
      }}}
]
```
</details>

### Sending the Tool Definition to the Model

Once you have defined your tool(s), you provide them to the LLM (Large Language Model) when making a Chat Completion request. Let’s break down the main parameters involved in this API call:

- **model**: Specifies which language model version to use (e.g., `""llama-3.3-70b-versatile""`). Different models may have different capabilities and costs.
- **messages**: A list of messages representing the conversation history. Each message is a dictionary with fields like ""role"" (either ""user"", ""assistant"", ""system"", or ""tool"") and ""content"" (the message text). Keeping the full chat history enables the LLM to generate coherent and contextually relevant responses.
- **tools**: The list of tool definitions provided to the LLM—these specify how to call function to get weather details.
- **tool_choice**: Determines whether the model decides automatically (""auto"") when to call a tool, or if you want to force a specific tool call.

Here’s how a complete request using these parameters might look:

<details>
<summary><strong>Code</strong></summary>

```python
from google.colab import userdata
from groq import Groq
import json
import requests

client = Groq(
    api_key = userdata.get('GROQ_API_KEY')
)

def get_weather(location):
 api_key = userdata.get('WEATHER_API_KEY')
 url = f""http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}""
 response = requests.get(url)
 data = response.json()

 if data[""cod""] == 200:
   return {
     ""location"": location,
     ""temperature"": data[""main""][""temp""],
     ""description"": data[""weather""][0][""description""]
   }
 else:
   return {""Oops! Something went wrong.""}

tools = [
  {
    ""type"": ""function"",
    ""function"": {
      ""name"": ""get_weather"",
      ""description"": ""Get current weather for a city"",
      ""parameters"": {
        ""type"": ""object"",
        ""properties"": {
          ""location"": {
            ""type"": ""string"",
            ""description"": ""City name like Mumbai, London""
            }
            },
      ""required"": [""location""]
           }
       }
   }
]

llm_messages = [
  {
    ""role"": ""system"",
    ""content"": ""You are a weather assistant. Use get_weather function when asked about weather.""
  },
  {
    ""role"": ""user"",
    ""content"": ""What's the weather in Mumbai?""
  }
]

response = client.chat.completions.create(
  model=""llama-3.3-70b-versatile"",
  messages=llm_messages,
  tools=tools,
  tool_choice=""auto""
)

print(response.choices[0].message)

```
- The model evaluates the user message. If it determines a tool call is needed, it includes the tool call in the response rather than a plain text answer.
- Otherwise, `.message.content` contains a direct natural language response from the LLM.
- Examining the full `response` lets you inspect tool call details or troubleshoot unexpected behavior.

</details>

### Understanding the LLM Response

<details>
<summary><strong>Tool Call(Response from LLM)</strong></summary>

```python
{
  ""id"": ""chatcmpl-8275582c-f79c-4af1-8f69-8bb8cfc5ba90"",
  ""choices"": [
    {
      ""finish_reason"": ""tool_calls"",
      ""index"": 0,
      ""logprobs"": null,
      ""message"": {
        ""content"": null,
        ""role"": ""assistant"",
        ""annotations"": null,
        ""executed_tools"": null,
        ""function_call"": null,
        ""reasoning"": null,
        ""tool_calls"": [
          {
            ""id"": ""y5nmt906p"",
            ""function"": {
              ""arguments"": ""{\""location\"":\""Hyderabad\""}"",
              ""name"": ""get_weather""
            },
            ""type"": ""function""
          }
        ]
      }
    }
  ],
  ""created"": 1766490111,
  ""model"": ""llama-3.3-70b-versatile"",
  ""object"": ""chat.completion"",
  ""mcp_list_tools"": null,
  ""service_tier"": ""on_demand"",
  ""system_fingerprint"": ""fp_93b5f9e564"",
  ""usage"": {
    ""completion_tokens"": 15,
    ""prompt_tokens"": 229,
    ""total_tokens"": 244,
    ""completion_time"": 0.045290652,
    ""completion_tokens_details"": null,
    ""prompt_time"": 0.011681956,
    ""prompt_tokens_details"": null,
    ""queue_time"": 0.008271432,
    ""total_time"": 0.056972608
  },
  ""usage_breakdown"": null,
  ""x_groq"": {
    ""id"": ""req_01kd5g7z11efkvagwg4xz2fy9c"",
    ""debug"": null,
    ""seed"": 1715653078,
    ""usage"": null
  }
}


```

</details>

Instead of directly returning weather information, the LLM may return a structured response requesting a tool.This response is called a **Tool Call**.


When the LLM decides to use a tool, it always returns structured information, including:

-   Function name to call
-   Parameters to use



### Step 3: Handle the LLM's Tool Call

When using tool/function calling, the LLM (Language Model) does **not** execute functions or access tools by itself. Instead, if it determines that an external tool (in this case, a function like `get_weather`) is needed to answer a user's question, it returns a special structured response called a **tool call**. This tool call specifies which function to run and with which parameters.

<details>
<summary><strong>First API Call and Handling the Response</strong></summary>

```python
from google.colab import userdata
from groq import Groq
import json
import requests

client = Groq(
    api_key = userdata.get('GROQ_API_KEY')
)

def get_weather(location):
 api_key = userdata.get('WEATHER_API_KEY')
 url = f""http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}""
 response = requests.get(url)
 data = response.json()

 if data[""cod""] == 200:
   return {
     ""location"": location,
     ""temperature"": data[""main""][""temp""],
     ""description"": data[""weather""][0][""description""]
   }
 else:
   return {""Oops! Something went wrong.""}

tools = [
  {
    ""type"": ""function"",
    ""function"": {
      ""name"": ""get_weather"",
      ""description"": ""Get current weather for a city"",
      ""parameters"": {
        ""type"": ""object"",
        ""properties"": {
          ""location"": {
            ""type"": ""string"",
            ""description"": ""City name like Mumbai, London""
            }
            },
      ""required"": [""location""]
           }
       }
   }
]

llm_messages = [
  {
    ""role"": ""system"",
    ""content"": ""You are a weather assistant. Use get_weather function when asked about weather.""
  },
  {
    ""role"": ""user"",
    ""content"": ""What's the weather in Mumbai?""
  }
]

response = client.chat.completions.create(
  model=""llama-3.3-70b-versatile"",
  messages=llm_messages,
  tools=tools,
  tool_choice=""auto""
)

response_message = response.choices[0].message

if response_message.tool_calls:
  tool_call = response_message.tool_calls[0]
  arguments = json.loads(tool_call.function.arguments)
  location = arguments['location']
  weather_data = get_weather(location)

  final_response = client.chat.completions.create(
      messages = llm_messages,
      model = ""llama-3.3-70b-versatile"",
      tools = tools,
      tool_choice = ""auto""
  )
```

- When the user asks for the weather, the LLM receives the message along with the tool definition (the schema of what can be called).
- Rather than trying to answer directly, the LLM may respond with a **tool call** indicating ""I want you to call `get_weather` with `{""location"": ""Mumbai""}`"".
- The code checks for this tool call, extracts the requested parameters from the tool call's arguments, and then executes the actual Python function (`get_weather`) outside of the LLM.
- This is necessary because LLMs can't access the internet, APIs, or your environment; you must run the code they suggest and then supply the result back to them.

</details>

### Step 4: Send the Results Back to the LLM

Once we've received the actual weather information from our `get_weather` function (stored in `weather_data`), we need to provide this result back to the LLM. The LLM can then use the returned data to generate a natural language response for the user.

We append the LLM's tool call request and our function's result to the message history, then make a final API call.

```python
llm_messages.append(response_message)

  llm_messages.append({
      ""role"": ""tool"",
      ""tool_call_id"": tool_call.id,
      ""content"": json.dumps(weather_data)
  })
 ```
<details>

<summary><strong>Final Code (Sending Tool Output and Getting the Final Response)</strong></summary>
 
```python
from google.colab import userdata
from groq import Groq
import json
import requests

client = Groq(
    api_key = userdata.get('GROQ_API_KEY')
)

def get_weather(location):
 api_key = userdata.get('WEATHER_API_KEY')
 url = f""http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}""
 response = requests.get(url)
 data = response.json()

 if data.get(""cod"") == 200:
    return json.dumps({
      ""location"": location,
      ""temperature"": data[""main""][""temp""],
      ""description"": data[""weather""][0][""description""]
    })
  else:
    return json.dumps({""Oops! Something went wrong.""})

tools = [
  {
    ""type"": ""function"",
    ""function"": {
      ""name"": ""get_weather"",
      ""description"": ""Get current weather for a city"",
      ""parameters"": {
        ""type"": ""object"",
        ""properties"": {
          ""location"": {
            ""type"": ""string"",
            ""description"": ""City name like Mumbai, London""
            }
            },
      ""required"": [""location""]
           }
       }
   }
]

llm_messages = [
  {
    ""role"": ""system"",
    ""content"": ""You are a weather assistant. Use get_weather function when asked about weather.""
  },
  {
    ""role"": ""user"",
    ""content"": ""What's the weather in Mumbai?""
  }
]

response = client.chat.completions.create(
  model=""llama-3.3-70b-versatile"",
  messages=llm_messages,
  tools=tools,
  tool_choice=""auto""
)

response_message = response.choices[0].message

if response_message.tool_calls:
  tool_call = response_message.tool_calls[0]
  arguments = json.loads(tool_call.function.arguments)
  location = arguments['location']
  weather_data = get_weather(location)

  llm_messages.append(response_message)

  llm_messages.append({
      ""role"": ""tool"",
      ""tool_call_id"": tool_call.id,
      ""content"": json.dumps(weather_data)
  })

  final_response = client.chat.completions.create(
      messages = llm_messages,
      model = ""llama-3.3-70b-versatile"",
      tools = tools,
      tool_choice = ""auto""
  )

  print(final_response.choices[0].message.content)
```
</details>
---

## Flow Summary

Here is a summary of the entire function calling flow:

1.  **Developer**: Defines a `get_weather` function in Python.
2.  **Developer**: Describes the function to the LLM using a JSON schema (the `tools` list).
3.  **User**: Asks, ""What’s the weather in Hyderabad?"".
4.  **LLM**: Receives the prompt and the tool definition. It decides the `get_weather` tool is needed and returns a tool call for `get_weather(""Hyderabad"")`.
5.  **Developer(get_weather Function code)**: Catches the tool call, executes the `get_weather(""Hyderabad"")` function, which calls the OpenWeatherMap API.
6.  **Developer(get_weather Function code)**: Sends this result back to the LLM in a new API call, including the full conversation history.
7.  **LLM**: Receives the temperature data and generates the final response: ""It’s currently 26°C in Hyderabad.""


---

# Effective Prompting Techniques

## Introduction

Effective prompting is crucial for getting the best results from Large Language Models (LLMs). When instructions are given in plain paragraphs, AI may miss details, skip steps, or format answers inconsistently. This guide covers several advanced techniques to help you create clear, structured, and powerful prompts.

---

## 1. Structured Prompting

Structured prompting is a method of writing prompts in formal formats like JSON or TOON to guide the AI in producing clear, organized, and consistent responses. Instead of guessing your intent, the model is told exactly what you want.

### Problem with Unstructured Prompts

When instructions are given in plain paragraphs, an AI might:

- Miss important details
- Skip steps in a multi-step task
- Format the output inconsistently

This can lead to incorrect, messy, or unpredictable results.

### Structured Prompting with JSON

Using JSON format in your prompts helps in defining the task and the desired output structure clearly.

**Example 1: Normal vs. JSON Prompt**

*   **Normal Prompt:**

    ```
    Provide summary about Generative AI in 300 words
    ```
*   **JSON Prompt:**

    ```json
    {
      ""task"": ""summarize_topic"",
      ""topic"": ""Generative AI"",
      ""style"": ""informative and clear"",
      ""length"": ""approximately 300 words""
    }
    ```
The JSON version is more explicit, leading to a crisper and more relevant response.

**Example 2: Data Extraction**

```json
{
  ""task"": ""extract_order_details"",
  ""output_format"": {
    ""customer_name"": """",
    ""phone"": """",
    ""product"": """",
    ""quantity"": """",
    ""delivery_location"": """"
  },
  ""text"": ""Hi, I want to order 2 iPhones for delivery to Bangalore. My name is Riya, phone number 9876543210.""
}
```

### When to Use Structured Prompting

1.  **Data extraction** for automation.
2.  When you want **accurate and clear responses**.
3.  When sending AI output to a **backend API or database**.
- When working with **Multi-step agent workflows**

### Benefits of Structured Prompting

- Makes AI answers organized and predictable.
- Minimizes errors and misinterpretations.
- Saves time in parsing and debugging the output.

### The TOON Format: A More Efficient Alternative

A problem with JSON is its verbosity. It uses a lot of punctuation (`{}`, `[]`, `""`, `:`, `,`) and repeats keys, which consumes more tokens and increases costs.

**Token-Oriented Object Notation (TOON)** is a lightweight format that uses minimal punctuation, reducing token count and cost.

**JSON vs. TOON Comparison**

 **Example:**
JSON prompt:

 ```json
 {
  ""task"": ""extract_order_details"",
  ""output_format"": {
    ""customer_name"": """",
    ""phone"": """",
    ""product"": """",
    ""quantity"": """",
    ""delivery_location"": """"
  },
  ""text"": ""Hi, I want to order 2 iPhones for delivery to Bangalore. My name is Riya, phone number 1234567890.""
} 
``` 
Tokens used in JSON Prompt: ~105-110

TOON Prompt:

```Toon
task: extract_order_details
fields[5]{customer_name,phone,product,quantity,delivery_location}:
Hi, I want to order 2 iPhones for delivery to Bangalore. My name is Riya, phone number 1234567890.

```
Tokens used in TOON Prompt: ~70-75

### Why TOON Produces Better Results

- **Schema Declared Once**: TOON lists all field names once.
- **Minimal Punctuation**: It uses CSV-style rows.
- **Explicit Array Length**: TOON shows (used [5] in the above example) to indicate the number of fields.

---

## 2. Meta Prompting

Meta-prompting involves using the language model itself to generate or improve prompts before you use them for the final task.

### Why Use Meta Prompting?

- Gets better, clearer, and more creative answers.
- Saves time by reducing trial-and-error with prompts.
- Helps with complex or multi-step problems

### Example 1


    You are an expert prompt engineer. Your task is to create an effective prompt for {generating product descriptions}. Consider including guidelines for tone, structure, and key elements to include. The prompt should instruct the AI to: {write compelling, accurate, and concise descriptions for 
    various products on an e-commerce website} 

    
    
### Example 2

Instead of a basic prompt, you use a meta-prompt to first generate a better prompt.

*   **Basic Prompt:**

    ```
    “Write an SEO-optimized blog about why LLMs are important
    ```
    
*   **Meta-prompt:**

    ```
    You are a wizard prompt engineer. You write very bespoke, detailed, and succinct prompts. I want you to write me a prompt that will {{ write a blog about importance of LLM with SEO optimization }}
    ```

The model will first generate a highly detailed prompt, which you can then use to get a superior final output.

---

## 3. Prompt Chaining

Prompt chaining is a technique where a task is broken down into a series of smaller prompts. The output from one prompt is used as the input for the next, guiding the model to produce a more coherent and accurate final result.


### Implementation Steps

1. Split the task into smaller, logical subtasks.
2. Write clear prompts for each step.
3. Pass the output of one step sequentially as input to the next.

### Example: Creating a Revision Sheet

**Task**: Create a summary of a topic, generate questions from it, and combine both into a final revision sheet.
**Example:**

- Initial Code:

```python
from google import genai
from google.colab import userdata

client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))

# Revision buddy Function
def revision_buddy(user_prompt):
    response = client.models.generate_content(
        model=""gemini-2.5-flash"",
        contents=user_prompt
    )
    return response.text
response = revision_buddy(""Explain about Generative AI"")
print(""Output:\n"", response)

```

1. Chain Step 1: Summarize the topic

```python
summary = revision_buddy(""Summarize Operating System basics in bullet points."")
print(""SUMMARY:\n"", summary)
```

2. Chain Step 2: Create Questions

Second step uses the result from the first step - this is Prompt Chaining

```python
questions = revision_buddy(f""Generate 5 exam questions from this summary:\n{summary}"")
print(""\nQUESTIONS:\n"", questions)
```

3. Chain Step 3: Create Final Revision Sheet

Subsequent step uses the result from previous steps — this is Prompt Chaining

```python
revision_sheet = revision_buddy(
    f""Create a final revision sheet using this summary and questions.\n""
    f""Summary:\n{summary}\nQuestions:\n{questions}""
)
print(""\nREVISION SHEET:\n"", revision_sheet)
```
---

## 4. Prompt Base

PromptBase is a marketplace website where people can buy and sell high-quality prompts for AI tools like ChatGPT, DALL-E, and Midjourney.

<MultiLineNote>
Free prompts are also available in PromptBase
</MultiLineNote>

### Getting Started on PromptBase

1.  **Make an account** in <a href=""https://promptbase.com/"" target=""_blank"">PromptBase</a> and set up your profile.
2.  **Upload prompts** that are clear, creative, and have been tested.
3.  **Use relevant keywords** so people can find your prompts easily.

---

## 5. General Effective Prompting Tips

### Clarity
Use simple and clear wording so the AI understands exactly what you want.

*   **Generic Prompt:** “Describe a cell”
*   **Precise Prompt:** “Describe the parts of a human cell in 3 sentences: nucleus, cytoplasm, and membrane”

### Specificity
Add details like length, tone, or format to get a more precise answer.

*   **Generic Prompt:** “Write a story”
*   **Precise Prompt:** “Write a 500-word detective story set in London in the 1920s about a missing painting”

### Contextual Awareness
Give background information, such as who the answer is for (audience), what role the AI should play, or the situation.

*   **Generic Prompt:** “What are the causes of the French Revolution?”
*   **Precise Prompt:** “You are a high school teacher. Explain 3 causes of the French Revolution in simple words for students”

### Output Guidance
Tell the AI the exact format or structure you expect in the output.

*   **Generic Prompt:** “Compare iPhone and Android”
*   **Precise Prompt:** “Make a comparison table with columns for price, features, and ecosystem, then add a 2-sentence conclusion”

### Adaptability
Use reusable prompt templates for consistent results across similar tasks.

*   **Template:** 

```
Summarize [topic] in 3 bullet points for [audience]. Add one real-world example.
```

---



# Introduction to LangChain

## Introduction

In this unit, we will understand the challenges involved in building LLM applications and why a framework like LangChain is needed. We’ll explore how LangChain simplifies working with different LLM providers and learn about its core components. We will then focus on key components such as Models and Messages, and see how they help structure interactions with LLMs in a clean and consistent way.

### Manual and Repetitive Tasks in LLM Development
When working directly with LLM providers, developers are required to perform several repetitive tasks manually:

*   Rewrite tool schemas for different providers
*   Manage entire conversation flow manually
*   Handle tool execution logic ourselves
*   Format and structure model response

### The Provider Problem

Consider an application built using an LLM from Groq, such as the Weather Application. While the application works well with Groq, challenges arise when there is a need to, Switch to Claude (Anthropic), Gemini (Google), GPT-5 (OpenAI).

### Challenges in Switching Between Models
Switching from one LLM provider to another introduces multiple technical differences:

*   Different API structures
*   Different response formats
*   Different ways to handle tool calling
*   Different message formatting requirements

As a result, significant portions of the application code must be rewritten for each provider change.

### Growing Complexity in LLM Applications
As LLM applications evolve, additional requirements increases overall complexity.

Common challenges include:

*   Adding conversation memory
*   Integrating multiple tools
*   Handling errors

### Limitations of Implementing from Scratch
Building and maintaining LLM applications without a framework is:

*   Time-consuming
*   Error-prone
*   Difficult to maintain
*   Hard to scale

## Solution: We Need a Framework

A framework should:

*   Standardize working with different LLM providers
*   Provide pre-built components for common tasks
*   Enable easy switching between models and tools
*   Handle repetitive code automatically
*   Be well-tested and community-maintained

### Popular Frameworks available for building LLM Applications

*   LangChain
*   LlamaIndex
*   Haystack
*   Semantic Kernel
*   CrewAI

## What is LangChain?

LangChain is the easiest way to start building agents and applications powered by LLMs. It provides pre-built, modular components and standardized interfaces to build LLM applications quickly and efficiently.

### Why LangChain?
*   Most Widely Adopted: Over 1,20,000+ GitHub stars, used by thousands of companies.
*   Integrations for 100+ LLM Providers.

### LangChain Features
*   Comprehensive Documentation: LangChain has extensive tutorials, <a href=""https://docs.langchain.com/oss/python/langchain/overview"" target=""_blank"">documentation</a> and active community support.
*   Modular and Flexible: Use what you need, extend when necessary.

### Advantages of LangChain
*   Standardized Interfaces and Modularity
*   External Data Integration (RAG)
*   Agentic Capabilities and Automation
*   Active Community and Resources

### LangChain Core Components
*   Models
*   Messages
*   Tools
*   Agents

There are many more components present in LangChain.

## Models
LangChain’s standard model interfaces give us access to 100+ provider integrations, making it easy to experiment with and switch between models.

### Gemini model integration using LangChain

#### 1. Setting Up Environment
1.  Open <a href=""https://colab.research.google.com/"" target=""_blank"">Google Colab</a>
2.  Create a new notebook

<MultiLineNote>
Ensure you have a Google account created
</MultiLineNote>
#### 2.Installing the required pacakges
General Syntax(To install any LLM provider pacakge):

```bash
!pip install -U langchain-[provider-name]
```
Installing the `langchain-google-genai` package:

```bash
!pip install -U langchain-google-genai
```

#### 3. Securing the Gemini API Key
We will use Colab Secrets to hide our Gemini API Key from our code to use it securely.

#### 4. Configure the Gemini Model

```python
from google.colab import userdata
api_key=userdata.get('GEMINI_API_KEY')
```

#### 5. Importing Chat Model
LangChain provides `init_chat_model` to initialize chat from a chat model provider of our choice (e.g., Gemini).

```python
from langchain.chat_models import init_chat_model
```

#### Syntax:
```python
model = init_chat_model(
  <llm_provider_name>:<model-name>,  
  api_key=api_key,
)
```

#### Parameters
A chat model takes parameters that can be used to configure its behavior:


*   `llm_provider_name`: The name or identifier of the specific llm provider.
*   `model`: The name or identifier of the specific model you want to use with a provider.
*   `api_key`: The key required for authenticating with the model’s provider.


#### Initializing the Chat Model (Gemini Example)

```python
model = init_chat_model(
  ""google_genai:gemini-2.5-flash"",
  api_key=api_key,
)
```

#### 6. Making Request to the Model
LangChain provides `invoke()` method to make a request to the model with a single message or a list of messages.

```python
response = model.invoke(""What are AI Agents?"")
print(response)
```

#### Code to make a request to gemini-2.5-flash (gemini models) using LangChain

```python
from google.colab import userdata
api_key=userdata.get('GEMINI_API_KEY')

from langchain.chat_models import init_chat_model
model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=api_key,

)
response = model.invoke(""What are AI Agents?"")
print(response)
```

## Messages

Messages are the fundamental unit of context for models in LangChain. They represent the input and output of models.

Messages are Objects that contains:

*   **Role**: Identifies the message type.
*   **Content**: Represents the actual content of the message.
*   **Metadata**: Optional fields such as response information, message IDs, and token usage.

#### Message Types
1.  System Message
2.  Human Message
3.  AI Message
4.  Tool Message

#### 1. Importing the HumanMessage and SystemMessage 

This step imports the message classes used by LangChain to represent different roles in a conversation. These message objects help structure the input sent to the chat model.

```python
from langchain.messages import HumanMessage, SystemMessage
```

#### 2. Creating a SystemMessage(System Prompt) 

The `SystemMessage` is used to define the behavior or role of the model. 

```python
system_msg = SystemMessage(""You are a helpful assistant."")
```

#### 3. Creating a HumanMessage(User Query) 
The `HumanMessage` represents the user’s input or question that will be processed by the chat model.

```python
human_msg = HumanMessage(""What are AI Agents?"")
```

#### 4. Storing SystemMessage and HumanMessage in a list

```python
system_msg = SystemMessage(""You are a helpful assistant."")
human_msg = HumanMessage(""What are AI Agents?"")
messages = [system_msg, human_msg]
```

### Final Code to make a request to gemini-2.5-flash (gemini models) using LangChain
The following code shows how to combine system and human messages, initialize the Gemini chat model using LangChain, and invoke the model with structured message input.

```python
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from google.colab import userdata
api_key=userdata.get('GEMINI_API_KEY')

system_msg = SystemMessage(""You are a helpful assistant."")
human_msg = HumanMessage(""What are Ai Agents?"")
messages = [system_msg, human_msg]

model = init_chat_model(
  ""google_genai:gemini-2.5-flash"",
  api_key=api_key,
)

response = model.invoke(messages)
print(response.content)
```

### Final Code to make a request to llama-3.3-70b-versatile (LLM hosted in groq) using LangChain

The `langchain-groq` package is required to enable LangChain to communicate with LLMs present in Groq. It provides the necessary functionality to call models present in Groq using langchain.

1. Installing the `langchain-groq` package:

```bash
!pip install -U langchain-groq
```

<MultiLineNote>
Ensure you have a <a href=""https://console.groq.com/keys"" target=""_blank"">Groq API key</a> and place it in your Colab Secrets.</MultiLineNote>
This code initializes a llama-3.3-70b-versatile present in Groq using LangChain, securely loads the Groq API key from Colab Secrets, and sends structured system and user messages to the model.

```python
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from google.colab import userdata
api_key=userdata.get('GROQ_API_KEY')

system_msg = SystemMessage(""You are a helpful assistant."")
human_msg = HumanMessage(""What are Ai Agents?"")
messages = [system_msg, human_msg]

model = init_chat_model(
  ""groq:llama-3.3-70b-versatile"",
  api_key=api_key,
)

response = model.invoke(messages)
print(response.content)
```

### Final Code to make a request to gpt-4.1 (openai models) using LangChain

The `langchain-openai` package is required to enable LangChain to communicate with OpenAI models. It provides the necessary functionality to initialize and invoke OpenAI models using LangChain.

1.Installing the `langchain-openai` package:

```bash
!pip install -U langchain-openai
```
<MultiLineNote> 
OpenAI APIs are not free to use. You need a paid OpenAI account to generate an <a href=""https://platform.openai.com/settings/organization/api-keys"" target=""_blank"">OpenAI API key</a> and place it in your Colab Secrets.</MultiLineNote>
This code initializes the gpt-4.1 model available from OpenAI using LangChain, securely loads the OpenAI API key from Colab Secrets, and sends structured system and user messages to the model.

```python
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from google.colab import userdata
api_key=userdata.get('OPENAI_API_KEY')

system_msg = SystemMessage(""You are a helpful assistant."")
human_msg = HumanMessage(""What are Ai Agents?"")
messages = [system_msg, human_msg]

model = init_chat_model(
  ""openai:gpt-4.1"",
  api_key=api_key,
)

response = model.invoke(messages)
print(response.content)
```

As we build more advanced applications, we will be working with new components like Tools,Agents and other components in the LangChain ecosystem.

---

# Introduction to Retrieval-Augmented Generation | Part 1

## Introduction

Imagine asking a Large Language Model (LLM) questions about your private documents:

-   What topics are in my university's Gen AI syllabus?
-   Summarize Attention Is All You Need research paper (without uploading the actual paper)
-   What's my college's leave policy?
-   Explain Chapter 5 in Gen AI (Without sharing the textbook)

LLMs are trained on massive amounts of public data, but they can't answer these questions because they don't have access to your personal or confidential documents.

### The Problem: Generic vs. Specific Information

If you ask an LLM a question that requires specific knowledge, you get a generic explanation from multiple sources across the internet. What you actually need are answers from **your** documents, not from generic internet data. The AI might give a confident answer, but it may not match what your specific document contains.

This is because of the following limitations of LLM's:

1.  **Knowledge Cutoff**: LLMs are trained on data available up to a certain point in time and do not have awareness of information created or updated after that training period.
2.  **Hallucinations**: When reliable information is missing, LLMs may generate responses that sound confident but are factually incorrect or not grounded in real data.
3.  **No Access to Private Data**: They cannot access your local files, internal wikis, or databases.

---

## Solutions to Overcome LLM Limitations

### 1. Give Context in Your Prompt

Manually add important information related to your question before asking the LLM.

```
""You are a helpful assistant. Answer the question ONLY from the provided context. If the context is insufficient, just say you don’t know.

{context}

Question: {question}""
```

**Advantages of giving context in the Prompt:**

-   No setup needed, works immediately.
-   Free to use.
-   Easy to implement.

**Disadvantages of giving context in the Prompt:**

-   Documents can be very long, you cannot paste everything.
-   LLMs have a limited context size.
-   Not practical when you have multiple documents.


### 2. Fine-Tune the LLM

Fine-tune the LLM using your specific documents so the knowledge becomes part of the model.


**Advantages of Fine Tuning the LLM:**

-   Model becomes an expert on your documents.
-   Fast responses because the knowledge is already built-in.
-   No need to include context in the prompt.

**Disadvantages of Fine Tuning the LLM:**

-   Expensive and computationally intensive.
-   Takes significant time to fine-tune.
-   If data changes, the model needs to be fine-tuned again.
</details>

---

## Retrieval-Augmented Generation (RAG)

**Retrieval-Augmented Generation (RAG)** is the process of optimizing the output of an LLM so it references an authoritative knowledge base outside of its training data sources before generating a response.

The process is broken down into three steps:

-   **(R)ETRIEVE**: Retrieve the most relevant information from your documents.
-   **(A)UGMENT**: Augment (add) that information to the user's question.
-   **(G)ENERATE**: Generate a better answer using both the retrieved information and the LLM's knowledge.

### How RAG Works

![DocuChat flow](https://s3.ap-south-1.amazonaws.com/new-assets.ccbp.in/frontend/loading-data/niat-course-projects/Introduction%20to%20RAG%20_%20Part%201.png)

### Benefits of RAG
-   **Current Information**: Answers are based on up to date data.
-   **Decreased Hallucinations**: Responses are grounded in provided facts.
-   **Enhanced Accuracy**: Delivers more precise and relevant answers.
-   **Increased User Trust**: Users can see the source of the information.
-   **Domain-Specific**: Becomes an expert on a specific subject matter.

### Applications of RAG
-   Customer Support Chatbots
-   Financial Report Analysis
-   Medical Diagnosis Support
-   Legal Research Assistant
-   Enterprise Knowledge Search
-   Banking Policy Assistant
-   Employee Onboarding Assistant
-   Educational Tutoring
-   Video Content Chat

---

## Building DocuChat Application

**Scenario**: You have a 40-page research paper to read before tomorrow's seminar, but you need quick answers to questions like:

-   What are the key findings?
-   What are the limitations and future scope?
-   What is the main contribution of this paper?

For this, we will use the famous paper that introduced Transformers: <a href=""https://arxiv.org/pdf/1706.03762.pdf"" target=""_blank"">Attention Is All You Need</a>.

### Why Not Just Copy-Paste into an LLM?

LLMs have limited **context windows**, they cannot process entire documents at once. Even if they could, finding specific information buried in pages of text is inefficient. This is where RAG helps.

**DocuChat** will be a RAG-powered Q&A assistant that:
1.  **Retrieves** only the relevant paragraphs for your question.
2.  **Augments** your question with the actual paper content.
3.  **Generates** accurate answers grounded in the document.

### Frameworks for Building RAG Applications

Many frameworks simplify building RAG applications, including:

-   LangChain
-   LlamaIndex
-   Haystack
-   EmbedChain

We will use **LangChain**, as it simplifies the development process by providing a modular, standardized way to connect LLMs with external data sources.

### Building a RAG chatbot involves two main steps:
1.  **Indexing**: Preparing the documents for searching.
2.  **Retrieval and Generation**: Finding relevant data and generating an answer.

![DocuChat flow](https://s3.ap-south-1.amazonaws.com/new-assets.ccbp.in/frontend/loading-data/niat-course-projects/Introduction%20to%20RAG%20_%20Part%201%20%282%29.png)

## 1. RAG Indexing

Indexing ensures that your external documents are organized into a multiple smaller parts, such that it can be quickly searched

Think of it like a librarian organizing a library:

- **Load :** Ingest documents from various sources so they are available for processing.

- **Split :** Break documents into smaller, structured sections to make them easier to search.

- **Embed :** Convert document sections into embeddings.

- **Store :** Store them in a searchable index for efficient retrieval.

Think of indexing like how a librarian organizes a library so books can be found quickly.

### RAG Indexing: Library Example

**Without Indexing**
Imagine walking into a library where books are not organized at all. When you ask,

*“Do you have a book on Generative AI?”*

the librarian has no catalog to refer to and must search through every shelf manually. Finding the book can take **hours**, even if it exists.

**With Indexing**
Now imagine a well-organized library:

* **Load** – The librarian first **collects all the books** available in the library.
* **Split** – The books are then **organized by subject and placed onto appropriate shelves**, making them easier to locate.
* **Embed** – A **searchable catalog** is created that records where each book or topic is located.
* **Store** – This catalog is **stored in the system** so it can be queried instantly.

When you ask again,

*“Do you have a book on Generative AI?”*

the librarian simply checks the catalog, walks directly to the correct shelf, and hands you the book **within seconds**.

This is exactly how **RAG indexing** works—by organizing documents in advance so relevant information can be retrieved quickly and efficiently when a question is asked.

### Step 1: Load the Document

LangChain provides over 100 **Document Loaders** for various file formats (`.pdf`, `.docx`, `.csv`) and sources (Google Drive, Webpages, Databases).

| Category  | Loaders                                      | Use Cases            |
|----------|-----------------------------------------------|----------------------|
| Files    | TextLoader, PDFLoader, DocxLoader, CSVLoader  | Local documents      |
| Webpages | WebBaseLoader, PlaywrightURLLoader             | Scraping websites    |
| Cloud    | GoogleDriveLoader, OneDriveLoader, S3Loader    | Cloud storage        |
| Databases| SQLDatabaseLoader, MongoDBLoader               | Querying databases   |

#### Setting Up the Environment

1.  Go to <a href=""https://colab.research.google.com/"" target=""_blank"" rel=""noopener noreferrer"">Google Colab</a>
2.  Create a new notebook.
<MultiLineNote>
Ensure you have a Google account created.
</MultiLineNote>

#### Install Dependencies
Our research paper is in PDF format, so we'll use `PyPDFLoader`.

- `langchain-community` is needed because it contains the tools (like PyPDFLoader) that help LangChain read documents such as PDFs.
- `pypdf` is needed because it actually opens the PDF file and extracts the text from it.

```bash
!pip install -qU langchain-community pypdf
```

#### Loading the PDF

The `PyPDFLoader` reads a PDF file and extracts the text content page by page.

- Specifying the PDF file path, creating a loader for the file, and loading the PDF by converting each page into a separate Document object.

```python
from langchain_community.document_loaders import PyPDFLoader

# Make sure you have uploaded the PDF to your Colab environment
file_path = ""./attention_all_you_need.pdf""
loader = PyPDFLoader(file_path)
doc = loader.load()
```

- Printing the full list of documents created from the PDF, showing that the file has been successfully loaded.

```python
print(doc)
```

- Displaying metadata for the first page, such as:

    - Source file name
    - Page number
    - Total number of pages

```python
print(doc[0].metadata)
```

- Printing the actual text content extracted from the first page of the PDF.

```python
print(doc[0].page_content)
```

### Step 2: Split the Document

The loaded document pages are still too long for an LLM to process efficiently. We need to split them into smaller, meaningful chunks.

**Splitting** is the process of breaking large documents into smaller pieces so the retriever can effectively find relevant information. This respects LLM context window limits and improves retrieval accuracy.

**Advantages of Splitting: **

- Efficient Retrieval
- LLM Context Window Limits
- Improved Accuracy & Relevance
- Cost & Latency
- Semantic Coherence

#### **Different Ways of Splitting Documents**

1. **Length-Based Splitting**

    - This approach splits documents purely based on length, resulting in consistent chunk sizes.While simple and predictable, it may cut text in the middle of sentences or ideas.

2. **Text Structure-Based Splitting**

    - This strategy uses a hierarchy of natural text boundaries, trying each level in order:

        - Paragraphs (\n\n) — tried first
        - Sentences (., !, ?)
        - Words (spaces)
        - Characters

By respecting natural language structure whenever possible, this method helps preserve semantic coherence.

3. **Document Structure-Based Splitting**

    - For structured documents such as HTML, Markdown, or JSON, splitting is done based on their inherent structure. This keeps related content together and maintains logical grouping.

LangChain offers several **Text Splitters**,

| Text Splitter | How It Works |
|--------------|--------------|
| RecursiveCharacterTextSplitter | Splits on paragraphs, sentences, and words |
| CharacterTextSplitter | Splits on fixed character count |
| TokenTextSplitter | Splits based on token count |
| MarkdownTextSplitter | Respects markdown structure |
| PythonCodeTextSplitter | Respects code syntax |
| HTMLTextSplitter | Respects HTML tags |


We will use the `RecursiveCharacterTextSplitter`, which is great for generic text as it tries to split based on natural boundaries (paragraphs, sentences, words).

#### Install Dependencies
```bash
!pip install -qU langchain-text-splitters
```

#### Configure and Split
We'll split the document into chunks of 1000 characters with a 200-character overlap to maintain context between chunks.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
  chunk_size=1000,      
  chunk_overlap=200,    
)
all_splits = text_splitter.split_documents(doc)
print(all_splits)
print(f""Paper split into {len(all_splits)} sub-documents."")
print(f""Metadata: {all_splits[0].metadata}"")
```

- <a href=""https://colab.research.google.com/drive/1z7udEz5xr_HQswcGvB7bsdIt0556a69P#scrollTo=2q0NhFa7Hsf-"" target=""_blank"">Final Code</a>"

---

# Introduction to Retrieval-Augmented Generation | Part 2

In the previous unit, we covered LLM Limitations, Building a RAG Application, and RAG Indexing (loading and splitting documents). In this unit, we will focus on creating embeddings, storing them in a vector database, retrieving relevant chunks, and generating a final response using a Large Language Model (LLM).


## Introduction to RAG: Indexing

The first step is to **index** your documents for easy retrieval. This includes:

- **Loading the document**
- **Splitting** it into manageable chunks
- **Creating embeddings** that convert text into numerical representations
- **Storing** these embeddings in a vector store

##Create Embeddings
We have split our document into multiple chunks. Each split contains a portion of our document's information



**Challenge** -  How do we quickly find relevant chunks when a user asks a question?
**Solution** - We convert chunks into numbers (embeddings) that let us search by meaning instantly

### How it works

- Convert text into numbers (vectors)
- Compare vectors mathematically
- Vectors that are closer in value => Text that is closer in meaning

###What Are Embeddings
Embedding model converts text into numerical vectors (embeddings) that capture semantic meaning

**Similar meanings = Similar vectors**

###Embedding Models in LangChain

LangChain supports many embedding providers:

| Provider        | Model Examples           |
|-----------------|--------------------------|
| OpenAI          | text-embedding-3-small   |
| Cohere          | embed-english-v3.0       |
| HuggingFace     | all-mpnet-base-v2        |
| Google Vertex   | textembedding-gecko      |
| Ollama          | nomic-embed-text         |
| Voyage AI       | voyage-2                 |

###Why we Choose Hugging Face

- Completely free
- High quality
- Privacy

##Install Dependencies

```python
! pip install -qU langchain langchain-huggingface sentence_transformers

```
## Initialize Embeddings

```python
! pip install -qU  langchain langchain-huggingface sentence_transformers

from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
  model_name = ""sentence-transformers/all-mpnet-base-v2""
)

```

##Why We Need a Vector Store

Now we need to create and store embeddings so that we can search later.

### Create Embeddings
- Convert each split into a vector.

For example, we split a document into smaller parts and create embeddings for each part. These embeddings are numerical vectors representing the semantic meaning of the content.

- Example vectors from splits:
  - `[0.3, 0.4, 0.1, 1.8, 1.1...]`
  - `[0.7, 1.4, 2.1, 4.8, 1.8...]`
  - `[1.2, 0.3, 1.2, 4.1, 1.8...]`

### Store Embeddings
- Save all vectors in a Vector Store (a database for embeddings).

Once the embeddings are created, they are stored in a vector database. The vectors can later be retrieved for similarity comparisons or answering queries.

- Example stored vectors:
  - `[0.3, 0.4, 0.1, 1.8, 1.1...]`
  - `[0.7, 1.4, 2.1, 4.8, 1.8...]`
  - `[1.2, 0.3, 1.2, 4.1, 1.8...]`

##What is Vector Store

A vector store is a specialized storage system

- Stores vectors along with their metadata
- Allows quick searching by similarity
- Returns results ranked by how similar they are

##Vector Store Providers

- ChromaDB
- FAISS
- Pinecone
- Weaviate
- Qdrant
- Milvus
- Astra DB

LangChain provides a unified interface for vector stores

- Add documents to the store
- Remove stored documents by ID
- Query for semantically similar documents

###Install Dependencies

```python
!pip install -qU langchain-chroma

```

###Initialize ChromaDB

```python
from langchain_chroma import Chroma

vector_store = Chroma(
  collection_name=""research_collection"",      
  embedding_function=embedding_model,            
  persist_directory=""./chroma_langchain_db"" 
)
document_ids = vector_store.add_documents(documents=all_splits)

sample = vector_store.get(limit=1, include=[""embeddings"", ""documents""])
print(sample)
print(document_ids[:3])
```


### Save to Vector Store

#### What Gets Created

- **Your Project Folder/**
  - `chroma_langchain_db/`
    - chroma.sqlite3 – `Database file`
  - `attention_is_all_you_need.pdf` – `Collection data`

## RAG: Indexing

Now our document is indexed and stored !

- The actual RAG process, which takes the user query at run time and retrieves the relevant data from the index, then passes that to the model

Steps to be Followed

- Retrieve relevant Chunks
- Generate answers using LLM

## Retrieving Relevant Chunks

###The Goal

- Our vector store contains chunks from the research paper 

###The Challenge

- Which chunks contain the answer? We need to find the relevant chunks  to our question

###How Do We Find Relevant Chunk 

- User question converted to embedding
- Embedding compared with stored embeddings 
- Similar embeddings are identified
- Corresponding text chunks are returned

###What is Similarity Scoring

- The retriever uses cosine similarity a mathematical way to measure how close two vectors are in meaning-space

## Retrieve Relevant Chunks

### What is Similarity Scoring

**Imagine Two Arrows (Vectors):**

#### If they point the SAME direction  
Similarity = 1.0 (100% match)

#### If they point OPPOSITE directions  
Similarity = -1.0 (opposite meaning)

#### If they point somewhat the same way  
Similarity = 0.75 (75% match)

- The system now compares the question vector with all chunk vectors in the database

###Similarity Search Method

Similarity search method is a technique used to find and retrieve pieces of data that are semantically (by meaning) similar to a given query, rather than matching by exact keywords

<b> `vector_store.similarity_search(query, k=2) `</b>

k=2 Finds top 2 most similar chunks

####Building the Retrieval Function

```python
def retrieve_context(query: str, k: int = 2):
  retrieved_docs = vector_store.similarity_search(query, k=k)
```

####Extracting Document Content

```Python
def retrieve_context(query: str, k: int = 2):
  retrieved_docs = vector_store.similarity_search(query, k=k)

  docs_content = """"
  for doc in retrieved_docs:
    docs_content += f""Source: {doc.metadata}\n""
    docs_content += f""Content: {doc.page_content}\n\n""

  return docs_content, retrieved_docs
```

###Retrieved Chunks Alone Aren't Enough

- Raw text needs to be synthesized
- Information needs to be explained clearly
- Answer should be natural and conversational

##Generate answers using LLM

####The LLM’s Role

- Read the retrieved context
- Understand the user's question
- Generate accurate answer

###Installing Dependencies

<b>syntax</b>

```syntax
!pip install -U langchain-[provider-name]
```

```Python
!pip install -U langchain-google-genai

```

###Initializing The Model

```python 
from langchain.chat_models import init_chat_model
from google.colab import userdata

api_key = userdata.get('GEMINI_API_KEY')
model = init_chat_model(
   ""google_genai:gemini-2.5-flash"",
   api_key=api_key,
)
```

###Defining the Query function

```python
from langchain.chat_models import init_chat_model
from google.colab import userdata

api_key = userdata.get('GEMINI_API_KEY')
model = init_chat_model(
   ""google_genai:gemini-2.5-flash"",
   api_key=api_key,
)

def docu_chat(user_query):
  context, source_docs = retrieve_context(user_query, k=2)
```

###Setting Up the LLM Instructions 

```python
from langchain.chat_models import init_chat_model
from google.colab import userdata

api_key = userdata.get('GEMINI_API_KEY')
model = init_chat_model(
   ""google_genai:gemini-2.5-flash"",
   api_key=api_key,
)

def docu_chat(user_query):
  context, source_docs = retrieve_context(user_query, k=2)
  system_message = f""""""You are a helpful chatbot.
                     Use only the following pieces of context to answer the 
                     question. Don't makeup any new information: {context} """"""

  messages = [
    {""role"": ""system"", ""content"": system_message},
    {""role"": ""user"", ""content"": user_query}
  ]
```

###Invoking LLM And Getting Results

```python
from langchain.chat_models import init_chat_model
from google.colab import userdata

api_key = userdata.get('GEMINI_API_KEY')
model = init_chat_model(
   ""google_genai:gemini-2.5-flash"",
   api_key=api_key,
)

def docu_chat(user_query):
  context, source_docs = retrieve_context(user_query, k=2)
  system_message = f""""""You are a helpful chatbot.
                     Use only the following pieces of context to answer the 
                     question. Don't makeup any new information: {context} """"""

  messages = [
    {""role"": ""system"", ""content"": system_message},
    {""role"": ""user"", ""content"": user_query}
  ]
  response = model.invoke(messages)
     return {
  ""answer"": response.content,
  ""source_documents"": source_docs,
  ""context_used"": context
}
result = docu_chat( ""Explain what is the use of decoders 
in transformers?"")
print(result)
print(result[""answer""])
```

##Complete DocuChat Flow

![DocuChat Overview](https://s3.ap-south-1.amazonaws.com/new-assets.ccbp.in/frontend/loading-data/niat-course-projects/docuchat.png)

## Try It Yourself

### Textbook Assistant
Any chapter from your textbook

- Explain binary search
- What are the types of joins in SQL?

### Notes Q&A Bot
Your own class notes

- What did we cover about arrays?
- Explain recursion from my notes

### Exam Question Bank Assistant
Previous year question papers

- What topics have most questions?
- Show questions on sorting algorithms

###Final code

```python
! pip install -qU  langchain langchain-huggingface sentence_transformers

from langchain_huggingface import HuggingFaceEmbeddings

# Initialize free, local embedding model
embeddings = HuggingFaceEmbeddings(
    model_name=""sentence-transformers/all-mpnet-base-v2""
)

```

```python
!pip install -qU langchain-chroma

from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name=""example_collection"",
    embedding_function=embeddings,
    persist_directory=""./chroma_langchain_db"",  # Where to save data locally, remove if not necessary
)
document_ids = vector_store.add_documents(documents=all_splits)
sample = vector_store.get(limit=1, include=[""embeddings"", ""documents""])
print(f""Embedding dimensions: {len(sample['embeddings'][0])}"")
print(sample)
print(document_ids[:3])
```

```python
from langchain.chat_models import init_chat_model
from google.colab import userdata

api_key = userdata.get('GEMINI_API_KEY')
model = init_chat_model(
   ""google_genai:gemini-2.5-flash"",
   api_key=api_key,
)

def docu_chat(user_query):
  context, source_docs = retrieve_context(user_query, k=2)
  system_message = f""""""You are a helpful chatbot.
                     Use only the following pieces of context to answer the 
                     question. Don't makeup any new information: {context} """"""

  messages = [
    {""role"": ""system"", ""content"": system_message},
    {""role"": ""user"", ""content"": user_query}
  ]
  response = model.invoke(messages)
     return {
  ""answer"": response.content,
  ""source_documents"": source_docs,
  ""context_used"": context
}
result = docu_chat( ""Explain what is the use of decoders in transformers?"")
print(result)
print(result[""answer""])
```
---

# Building AI Agents Using LangChain

In the previous units, we covered RAG applications and LangChain fundamentals. In this unit, we will learn how to build AI Agents that can autonomously perform tasks by using multiple tools. We'll build a practical **SkillMap Agent** that helps users understand skill demand in the industry and find matching job opportunities.

## What is an AI Agent?

An AI agent is a system that can operate independently to achieve a specific goal without constant human intervention.

### AI Agents Core Components

- **AI Model** (like GPT-5 or Claude): The reasoning engine that makes decisions
- **Tools** (search engines, databases, APIs): External capabilities the agent can use
- **Memory**: Ability to remember context across interactions

---

## Building SkillMap Agent

### The Problem

After learning a skill like Generative AI, common questions arise:

- What is the demand for Generative AI in the industry?
- Which roles require this skill?
- What jobs are available in India?

### The Current Approach

The typical approach is to search manually across multiple sources, getting scattered information from different articles, forums, and job portals. This is time-consuming and often gives incomplete results.

### The Solution

What if you could simply ask:

> ""What's the demand for Generative AI skills in the industry? Show me related job openings in India""

And get current market insights, real job openings, and easy-to-apply links all in one response?

This is exactly what our SkillMap Agent will do.

---

###Popular Frameworks for LLM Applications

- <b>LangChain</b>
- LlamaIndex
- Haystack
- Semantic Kernel
- CrewAI
<br> many more...

**LangChain**

It is a open source framework with a pre-built agent architecture and integrations for any model or tool — so you can build agents that adapt as fast as the ecosystem evolves

## SkillMap Agent Core Components


| Component | Purpose |
|-----------|---------|
| Google Gemini | AI reasoning and decision-making |
| Tavily Search | Getting skill demand information |
| JSearch (RapidAPI) | Getting live job links from LinkedIn, Indeed, Glassdoor |
| LangChain | Framework to orchestrate the agent |

---

## Steps to Build the SkillMap Agent

1. Creating the Agent
2. Creating the Skill Demand Search Tool
3. Creating the Job Search Tool
4. Defining System Prompt and Configuring Agent
5. Executing the Agent

---

## Step 1: Creating Agent using LangChain


LangChain provides a method called `create_agent` that lets us create an agent.

### create_agent() - Syntax

```python
agent = create_agent(
  model = model,
  tools = [//list of tools],
  system_prompt = system_prompt,
)
```

** create_agent**

The `create_agent` function creates an agent that calls tools in a loop until a stopping condition is met. The agent runs until the model emits a final output.

### Install LangChain

```python
!pip install langchain
```

```python
from langchain.agents import create_agent

agent = create_agent(
  model = model,
  tools = [//list of tools],
  system_prompt = system_prompt,
)
```
### Defining the Model

Models are the reasoning engine of agents. The model handles:

- The agent's decision-making process
- Determining which tools to call
- How to interpret results
- When to provide a final answer

### Initializing the Model

#### Install Google GenAI Package

```python
!pip install -U langchain-google-genai
```

```python
from langchain.chat_models import init_chat_model
from google.colab import userdata

google_api_key = userdata.get('GOOGLE_API_KEY')
model = init_chat_model(
    ""google_genai:gemini-2.5-flash"", 
    api_key=google_api_key
)
```

###Configuring the Model

```python
from langchain.agents import create_agent

agent = create_agent(
  model = model,  #The language model instance
  tools = [//list of tools],
  system_prompt = system_prompt,
)

```



---

## Step 2: Creating the Skill Demand Search Tool

### What Our Agent Needs

To provide useful career guidance, our agent needs to fetch real-time market insights like:

- Industry Demand
- Salary Trends
- Career Growth Opportunities

To retrieve this real-time market information, we need a search tool.

### LangChain Core Components
**Tools**

Tools are components that agents call to perform actions. They extend model capabilities by letting them interact with the world through well-defined inputs and outputs.

LangChain offers an extensive ecosystem with 1000+ tool integrations with different platforms.

###LangChain Tool Integrations

LangChain , Python Offers an extensive ecosystem with 1000+ tool integrations with different platforms

### Built-in Tool: Tavily Search

Tavily Search is a search engine built specifically for AI agents (LLMs) delivering real-time, accurate, and factual results at speed.

To find real-time market insights, we'll use Tavily Search.

### Install Tavily Package

```python
!pip install langchain-tavily
```

### Instantiate Tavily Search

- <a href=""https://app.tavily.com/home"" target=""_blank"">Tavily API Key</a>

```python
from langchain_tavily import TavilySearch
from google.colab import userdata

tavily_api_key = userdata.get('TAVILY_API_KEY')

skill_demand_tool = TavilySearch(
    max_results=5,
    search_depth=""advanced"",
    tavily_api_key=tavily_api_key
)
```

### Tavily Search Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| max_results | int | Maximum number of search results | 5 |
| search_depth | str | ""basic"" or ""advanced"" | ""basic"" |
| topic | str | ""general"", ""news"", or ""finance"" | ""general"" |

### Invocation Arguments

The Tavily search tool accepts the following argument during invocation:

- **query (required)** -> A natural language search query

### Testing the Skill Demand Tool

```python
result = skill_demand_tool.invoke({""query"": ""generative ai skills demand 2025""})
print(result)
```

---

## Step 3: Creating the Job Search Tool

### What We Need Next

We can now fetch skill demand and salary insights using Tavily Search. But that's only half the picture.

To make this truly useful, we also need to show actual job openings where this skill is required with direct apply links.

### Can Tavily Help Here?

| What We Need | Can Tavily Do It? |
|--------------|-------------------|
| Search skill demand trends | Yes |
| Get salary insights | Yes |
| Find actual job listings with apply links | No |
| Filter jobs by experience level (fresher/intern) | No |
| Get jobs from LinkedIn, Indeed, Glassdoor | No |

### Solution: Integrate with JSearch API

When built-in tools don't meet specific needs, we create Custom Tools.

To fetch live job listings, we'll integrate with RapidAPI's JSearch which gives us access to jobs from LinkedIn, Indeed, Glassdoor, and other major platforms.

### Understanding JSearch API

JSearch allows us to seamlessly access most up-to-date job postings and provides:

- Job titles and descriptions
- Company information
- Location details
- Application links
- Employment types

###Making HTTP Requests

Before creating our tool, let's understand what data the JSearch API returns

###Understanding JSearch Response

- <a href=""https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/playground/endpoint_1a4de4d7-7abd-4ec2-a897-57a0fc5ad496"" target=""_blank"">RapidAPI Key</a>

```python
import requests

rapidapi_key = userdata.get('RAPIDAPI_KEY')

url = ""https://jsearch.p.rapidapi.com/search""
headers = {
  ""x-rapidapi-key"": rapidapi_key,
  ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
}
querystring = {
  ""query"": ""Generative AI in India"",
  ""page"": ""1"",
  ""num_pages"": ""1""
}

response = requests.get(url, headers=headers, params=query_string)
print(response.json())

```

###Understanding the API Parameters


| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| query | String | Free-form job search query | ""software developer in India"" |
| country | String | ISO country code | ""in"" for India |
| employment_types | String | Comma-separated employment types | ""INTERN, FULLTIME"" |
| job requirements | String | Experience level filters | ""no experience,under 3 years experience"" |
| page | Number | Page to return (each page includes up to 10 results) | 1 |

###Built-in Tools

Tavily is a built-in tool in LangChain for web search, but for fetching live job listings from JSearch, we need     to create a custom tool


### Building a Custom Tool

LangChain provides many built-in tools, but for specific requirements like fetching live job listings, a ready-made tool might not exist. In such cases, LangChain lets us integrate our own custom tools.

The simplest way to create a Custom tool is with the `@tool` decorator. By default, the function's docstring becomes the tool's description that helps the model understand when to use it.

###Understanding Tool Syntax


```python
@tool
def function_name(parameter: str) -> str:
    """"""Short description of what this tool does.""""""
    return f""Processed: {parameter}""
```

- **Tool decorator (`@tool`)**: Registers the function as a LangChain tool
- **Type annotations**: Define the input schema and expected output type for the LLM
- **Docstring**: Describes the tool's purpose to help the LLM decide when to use it

### Import and Configure the Tool

```python
import requests
from langchain.tools import tool

@tool
def search_jobs(skill: str, location: str) -> list:
```

- Converts `search_jobs` into a tool the agent can call
- Agent will pass job skill and location as string inputs
- Returns a list of matching job results

### Define the Tool Description

```python
import requests
from langchain.tools import tool

@tool
def search_jobs(skill: str, location: str) -> list:
    """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
```

Helps the agent understand this tool searches jobs based on skill and location.

### Set Up API Credentials and Endpoint

```python
import requests
from langchain.tools import tool

@tool
def search_jobs(skill: str, location: str) -> list:
    """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
    print(f""\nCalling search_jobs tool"")
    print(f""Searching jobs for: {skill} in {location}"")

    rapidapi_key = userdata.get('RAPIDAPI_KEY')

    url = ""https://jsearch.p.rapidapi.com/search""
    headers = {
        ""x-rapidapi-key"": rapidapi_key,
        ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
    }
```

### Build Query Parameters

```python
@tool
def search_jobs(skill: str, location: str) -> list:
    """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
    print(f""\nCalling search_jobs tool"")
    print(f""Searching jobs for: {skill} in {location}"")

    rapidapi_key = userdata.get('RAPIDAPI_KEY')

    url = ""https://jsearch.p.rapidapi.com/search""
    headers = {
        ""x-rapidapi-key"": rapidapi_key,
        ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
    }
    querystring = {
        ""query"": f""{skill} in {location}"",
        ""page"": ""1"",
        ""country"": ""in"",
        ""employment_types"": ""INTERN,FULLTIME"",
        ""job_requirements"": ""no_experience,under_3_years_experience""
    }
```

### Make the API Call

```python
@tool
def search_jobs(skill: str, location: str) -> list:
    """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
    print(f""\nCalling search_jobs tool"")
    print(f""Searching jobs for: {skill} in {location}"")

    rapidapi_key = userdata.get('RAPIDAPI_KEY')

    url = ""https://jsearch.p.rapidapi.com/search""
    headers = {
        ""x-rapidapi-key"": rapidapi_key,
        ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
    }
    querystring = {
        ""query"": f""{skill} in {location}"",
        ""page"": ""1"",
        ""country"": ""in"",
        ""employment_types"": ""INTERN,FULLTIME"",
        ""job_requirements"": ""no_experience,under_3_years_experience""
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

```

### Extract Key Information

```python
@tool
def search_jobs(skill: str, location: str) -> list:
    """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
    print(f""\nCalling search_jobs tool"")
    print(f""Searching jobs for: {skill} in {location}"")

    rapidapi_key = userdata.get('RAPIDAPI_KEY')

    url = ""https://jsearch.p.rapidapi.com/search""
    headers = {
        ""x-rapidapi-key"": rapidapi_key,
        ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
    }
    querystring = {
        ""query"": f""{skill} in {location}"",
        ""page"": ""1"",
        ""country"": ""in"",
        ""employment_types"": ""INTERN,FULLTIME"",
        ""job_requirements"": ""no_experience,under_3_years_experience""
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    jobs = data.get(""data"", [])
    print(f""Found {len(jobs)} jobs\n"")

    result = []
    for job in jobs:
        result.append({
            ""title"": job.get(""job_title""),
            ""company"": job.get(""employer_name""),
            ""location"": job.get(""job_city""),
            ""apply_link"": job.get(""job_apply_link"")
        })
    return result
```

The `.get()` method retrieves data, returning an empty list if ""data"" doesn't exist.

---


###Creating the Job Search Tool (complete code)


```python
import requests
from langchain.tools import tool
from google.colab import userdata

@tool
def search_jobs(skill: str, location: str) -> list:
    """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
    print(f""\nCalling search_jobs tool"")
    print(f""Searching jobs for: {skill} in {location}"")

    rapidapi_key = userdata.get('RAPIDAPI_KEY')

    url = ""https://jsearch.p.rapidapi.com/search""
    headers = {
        ""x-rapidapi-key"": rapidapi_key,
        ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
    }
    querystring = {
        ""query"": f""{skill} in {location}"",
        ""page"": ""1"",
        ""country"": ""in"",
        ""employment_types"": ""INTERN,FULLTIME"",
        ""job_requirements"": ""no_experience,under_3_years_experience""
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    jobs = data.get(""data"", [])
    print(f""Found {len(jobs)} jobs\n"")

    result = []
    for job in jobs:
        result.append({
            ""title"": job.get(""job_title""),
            ""company"": job.get(""employer_name""),
            ""location"": job.get(""job_city""),
            ""apply_link"": job.get(""job_apply_link"")
        })
    return result
```

---

## Step 4: Defining System Prompt and Configuring Agent

### What We Have So Far

- `skill_demand_tool` (TavilySearch): Fetches market insights
- `search_jobs`: Fetches job listings

### What We Need Now

We have both tools ready. Now we need to tell the agent how to use these tools and what role it should play. This is done through a **System Prompt**.

We also need a language model that will act as the brain, deciding which tool to call and when.

### Define System Prompt

```python
system_prompt = """"""You are a Skill-to-Career Mapping assistant that helps students understand skill demand and find matching job opportunities.

You have access to these tools:
- skill_demand_tool: Search for industry demand, salary insights, and career trends
- search_jobs: Find actual job listings requiring specific skills

Help the student by researching the skill they ask about and finding relevant opportunities.

Present results in a clean, readable format with clear sections and proper spacing. Include all job details with apply links. Don't use markdown format.""""""
```

### Configuring System Prompt and Tools


```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[skill_demand_tool, search_jobs],
    system_prompt=system_prompt
)
```

###Removing Tool Invocations

```python
from langchain_tavily import TavilySearch
from google.colab import userdata

tavily_api_key = userdata.get('TAVILY_API_KEY')

skill_demand_tool = TavilySearch(
  max_results=5,
  search_depth=""advanced"",
  tavily_api_key=tavily_api_key
)

#Removing Tool Invocations
#result = skill_demand_tool.invoke({""query"": ""generative ai skills demand 2025""})
#print(result)

```
---

## Step 5: Executing the Agent

###create_agent Parameters

To execute our agent, we use the `invoke` method which triggers the complete workflow.

All agents include a sequence of messages in their state. To invoke the agent, pass a new message with the user's query.


### Run the Agent

All agents include a sequence of messages in their state -> To invoke the agent, pass a new message with the user's query


### Invoke the Agent

```python
user_query = ""What's the demand for generative ai in the industry and show me related job openings in India""

response = agent.invoke({
    ""messages"": [{""role"": ""user"", ""content"": user_query}]
})
```

### Getting the Response

```python
print(response[""messages""][-1].content)
```

- `response[""messages""]` contains the full conversation history
- `response[""messages""][-1]` is the agent's final message
- `.content` extracts the natural language response

---

<details>
<summary><strong>Final Code (Sending Tool Output and Getting the Final Response)</strong></summary>

```python
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain.tools import tool
import requests
from google.colab import userdata

# Initialize Google API key and model
google_api_key = userdata.get('GOOGLE_API_KEY')
model = init_chat_model(""google_genai:gemini-2.5-flash"", api_key=google_api_key)

# Initialize Tavily search tool
tavily_api_key = userdata.get('TAVILY_API_KEY')
skill_demand_tool = TavilySearch(
    max_results=5,
    search_depth=""advanced"",
    tavily_api_key=tavily_api_key,
)

# Invoke Tavily search tool
result = skill_demand_tool.invoke({""query"": ""generative ai skills demand 2025""})
print(result)

# Set up RapidAPI key and search jobs function
rapidapi_key = userdata.get('RAPIDAPI_KEY')

def search_jobs(skill: str, location: str) -> list:
    """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
    print(f""\nCalling search_jobs tool"")
    print(f""Searching jobs for: {skill} in {location}"")

    url = ""https://jsearch.p.rapidapi.com/search""
    headers = {
        ""x-rapidapi-key"": rapidapi_key,
        ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
    }
    querystring = {
        ""query"": f""{skill} in {location}"",
        ""page"": ""1"",
        ""country"": ""in"",
        ""employment_types"": ""INTERN,FULLTIME"",
        ""job_requirements"": ""no_experience,under_3_years_experience""
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    jobs = data.get(""data"", [])
    print(f""Found {len(jobs)} jobs\n"")

    # Format and return job results
    result = []
    for job in jobs:
        result.append({
            ""title"": job.get(""job_title""),
            ""company"": job.get(""employer_name""),
            ""location"": job.get(""job_city""),
            ""apply_link"": job.get(""job_apply_link"")
        })
    return result

# Define system prompt for the agent
system_prompt = """"""You are a Skill-to-Career Mapping assistant that helps students understand skill demand and find matching job opportunities.

You have access to these tools:
- skill_demand_tool: Search for industry demand, salary insights, and career trends
- search_jobs: Find actual job listings requiring specific skills

Help the student by researching the skill they ask about and finding relevant opportunities.

Present results in a clean, readable format with clear sections and proper spacing. Include all job details with apply links. Don't use markdown format.""""""

# Create and invoke LangChain agent
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[skill_demand_tool, search_jobs],
    system_prompt=system_prompt,
    debug=True
)

user_query = ""What's the demand for generative ai in the industry and show me related job openings in India""

response = agent.invoke({
    ""messages"": [{""role"": ""user"", ""content"": user_query}]
})
print(response[""messages""][-1].content)

```

</details>

---

## How the Agent Loop Works

1. **Start**: Agent node calls the model with current messages
2. **Decision**: The model checks whether tool calls are required
3. **If Yes**:
   - Execute the required tools
   - Add the tool results as a ToolMessage
   - Loop back and call the model again with updated messages
4. **If No**:
   - Return the final answer (without tool calls)
5. **End**

The process repeats until no more tool calls are needed. The agent returns the final answer with skill insights and job listings.

![Project Screenshot](https://s3.ap-south-1.amazonaws.com/new-assets.ccbp.in/frontend/loading-data/niat-course-projects/Pasted%20image.png)

---

## Try It Yourself

Challenge yourself by building similar agents:

| Agent Type | Input | What It Does |
|------------|-------|--------------|
| Interview Prep Agent | Role Name (e.g., ""Data Analyst"") | Find common interview questions + preparation tips |
| Salary Insights Agent | Job Title (e.g., ""Full Stack Developer"") | Fetch salary trends + top paying companies |
| Course Finder Agent | Skill name (e.g., ""Gen AI"") | Find free courses + certification options |
| Startup Jobs Agent | Domain (e.g., ""Fin Tech"") | Find startup job openings + company details |
| Skill Comparison Agent | Two skills (e.g., ""React vs Angular"") | Compare demand + job count + future scope |
| Location-Job Agent | City + Skill (e.g., ""Bangalore, Python"") | Find local jobs + remote options + avg salary |

You can also try replacing Tavily with other available search tools in LangChain like Brave Search, SearxNG Search, or Google Serper.

---

Here is the <a href=""https://colab.research.google.com/drive/1ZISgZ-DnOgzPHTjjSXBAjoLV_kaypWEO#scrollTo=NV7NBkLzROXQ"" target=""_blank"">
Building AI Agents with LangChain – Final Code
</a>

---

# Building Memory Agent using Langchain

## Introduction
In the previous session, we built the **SkillMap Agent** that helps to understand skill demand and find job openings.

Agents with memory are AI systems that can store and use past information to make better decisions in the present and future.

**Agent with memory = Large Language Model + Persistent Memory Store**

### Popular Types of Memory
1. **Short-Term Memory**
2. **Long-Term Memory**

### Short-Term Memory
Short-term memory refers to the model’s ability to remember information relevant to the current conversation or session.

* Recent messages
* Results from tool calls
* Task context

### Long-Term Memory
Long-term memory retains information across multiple sessions and interactions.

* User Preferences
* Interaction data
* Learned Behaviors

### Types of Long-Term Memory
Long-term memory can further be divided into three types:

1. **Episodic Memory**
2. **Procedural memory**
3. **Semantic memory**

---

## The Problem: Agent That Forgets
**Testing the SkillMap Agent**

* **User**: ""What's the demand for generative ai in the industry and show me related job openings in India""
* **Agent**: *Responds with GenAI demand info and job listings*
* **User**: ""Tell me more about the second job you showed""
* **Agent**: ""I don't have information about previous jobs. Could you specify which job?""

**Agent forgot the previous conversation!** Each invocation starts fresh with no access to previous conversations.

### Understanding Why Agents Forget
**Current Agent Behaviour**
Each `agent.invoke()` call is completely independent. There’s no connection between calls by default. Every time we call the agent, it is a **NEW** session.

### The Need for Persistence
We need to save the conversation somewhere, so the agent can look back.
Two questions arise:
1. Where do we save it?
2. How does the agent find the right conversation?

**This is where LangGraph helps us!**


### Various Options for persistence include:

* LangGraph Built-in Persistence - Checkpointers
* LangChain - RunnableWithMessageHistory 
* Custom Vector Database Integration
* External Memory Services - Mem0.ai/Zep


### What is LangGraph?
LangGraph is a low-level orchestration framework for building, managing, and deploying long-running, stateful agents.

* Built by LangChain Inc. (creators of LangChain).
* Focuses on state management and memory.
* Can be used independently OR with LangChain.

### LangGraph vs LangChain
* **LangGraph**: Low-level (state, memory, persistence, checkpoints).
* **LangChain**: High-level (create_agent, tools).

LangChain’s `create_agent()` is built on top of LangGraph. This means we can use LangGraph’s memory features directly with our agent.


### Types of Memory in LangGraph
* **Short-Term memory**: Short-term memory enables agents to track multi-turn conversations
* **Long-Term memory**: Long-term memory stores user-specific or application-specific data across conversations


## Implementing Short-term Memory for our Skill Map Agent

* **User**: ""Show me GenAI jobs""
* **Agent**: *Here are 5 jobs: Data Scientist, AI Engineer*
* **User**: ""Tell me about Job 2""
* **Agent**: *Here’s more about job : AI Engineer*

We want the agent to remember that ""AI Engineer"" refers to the second item in the previous list. To achieve this, we need something that can save messages automatically.

### Checkpointer
A Checkpointer is a mechanism that automatically saves the conversation state after each message. Each checkpoint contains the complete conversation history up to that point.

### Implementing Checkpointer

`InMemorySaver` is a simple checkpointer implementation that saves conversations in RAM.

* **What does it save?** All messages in the chat.
* **Where does it save?** In RAM (temporary).
* **When is it deleted?** When we refresh the session or stop the program.

<MultiLineNote>
`InMemorySaver` is for development only. For production, use **Persistent Checkpointers** such as:

* SqliteSaver
* PostgresSaver
</MultiLineNote>

### Import and Create Checkpointer Instance
```python
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()
```

### Add checkpointer to Agent
```python
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[skill_demand_tool, search_jobs],
    checkpointer=checkpointer  # ← Add this!
)
```
`checkpointer=checkpointer` tells LangGraph to enable persistence. Without it, the agent won't save any state.

---

## Finding the Right Conversation
Now that we're saving conversations, we need a way to identify them. 

### Thread_id
LangGraph uses the configurable dictionary to pass runtime parameters. The `thread_id` within it tells the checkpointer which conversation thread to use.

**config = {""configurable"": {""thread_id"": ""1""}}**
Think of it like a phone number for your chat:

* **Same thread_id** → Same conversation continues.
* **Different thread_id** → New conversation starts.


### Configuring thread_id
```python
config = {""configurable"": {""thread_id"": ""1""}}
```

### Using thread_id in Agent Invocation
```python
user_query = ""What's the demand for generative AI in the industry and show me related job openings in India""

response = agent.invoke({
  ""messages"": [{""role"": ""user"", ""content"": user_query}]
}, config=config)

print(response[""messages""][-1].content)
```
Using the same `config` (with the same `thread_id`) allows the agent to access previous messages in that conversation.

<details>
<summary>Final Code</summary>

```python
import requests
from google.colab import userdata
from langchain.tools import tool
from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

TAVILY_API_KEY = userdata.get(""TAVILY_API_KEY"")
RAPIDAPI_KEY = userdata.get(""RAPIDAPI_KEY"")
GOOGLE_API_KEY = userdata.get(""GOOGLE_API_KEY"")

skill_demand_tool = TavilySearch(
    max_results=5,
    search_depth=""advanced"",
    tavily_api_key=TAVILY_API_KEY,
)

@tool
def search_jobs(skill: str, location: str) -> list:
    """"""
    Search for jobs requiring a specific skill using the JSearch API.
    """"""
    print(""\nCalling search_jobs tool"")
    print(f""Searching jobs for: {skill} in {location}"")
    url = ""https://jsearch.p.rapidapi.com/search""
    headers = {
        ""x-rapidapi-key"": RAPIDAPI_KEY,
        ""x-rapidapi-host"": ""jsearch.p.rapidapi.com"",
    }
    params = {
        ""query"": f""{skill} in {location}"",
        ""page"": ""1"",
        ""num_pages"": ""1"",
        ""country"": ""in"",
        ""employment_types"": ""INTERN,FULLTIME"",
        ""job_requirements"": ""no_experience,under_3_years_experience"",
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    jobs = data.get(""data"", [])
    print(f""Found {len(jobs)} jobs\n"")
    return [
        {
            ""title"": job.get(""job_title""),
            ""company"": job.get(""employer_name""),
            ""location"": job.get(""job_city""),
            ""apply_link"": job.get(""job_apply_link""),
        }
        for job in jobs
    ]

SYSTEM_PROMPT = """"""
You are a Skill-to-Career Mapping assistant that helps students understand skill demand
and find matching job opportunities.

You have access to these tools:
- skill_demand_tool: Research industry demand, salary insights, and career trends
- search_jobs: Find real job listings based on skills and location

Present results in a clean, readable format with clear sections and spacing.
Include all job details with apply links.
Do not use markdown formatting.
""""""

model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=GOOGLE_API_KEY,
)

checkpointer = InMemorySaver()
config = {""configurable"": {""thread_id"": ""1""}}

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[skill_demand_tool, search_jobs],
    checkpointer=checkpointer,
    debug=True,
)

user_query = (
    ""What's the demand for generative AI in the industry ""
    ""and show me related job openings in India""
)

response = agent.invoke(
    {""messages"": [{""role"": ""user"", ""content"": user_query}]},
    config=config,
)

print(response[""messages""][-1].content[0][""text""])

user_query = ""Tell me more about the second job you showed""

response = agent.invoke(
    {""messages"": [{""role"": ""user"", ""content"": user_query}]},
    config=config,
)

print(response[""messages""][-1].content[0][""text""])

```
</details>
---

## Short Term Memory: Context Overflow
As conversation grows, problems arise:

* Exceeds LLM's context window.
* LLM gets ""distracted"" by old messages.
* Slower responses, higher costs.

### Context Overflow Strategies

* **Trim Messages**: Remove first few messages & retain last N messages.
* **Delete Messages**: Delete messages from LangGraph state permanently.
* **Summarize Messages**: Summarize earlier messages and replace them with a summary.
* **Custom Strategies**: Message filtering, etc.

---

# AI In The Real World

## Introduction

Till now, we've explored LLMs, RAG systems, Agents, and Memory. Now here's the exciting part: The concepts you just learned? They're already solving REAL problems for millions of people worldwide.

## What AI Can Do

### ChatGPT Identifies Rare Disease

A 4-year-old boy named Alex had chronic pain for 3 YEARS. 17 doctors couldn't figure it out. His mother copied symptoms and MRI results into ChatGPT which suggested ""This could be tethered cord syndrome."" A neurosurgeon confirmed it, surgery was performed, and the pain was gone.

<MultiLineQuickTip text={AI Concept}>

LLM pattern recognition from training data — same concept you learned!
</MultiLineQuickTip>

*   Full Story: <a href=""https://www.today.com/health/mom-chatgpt-diagnosis-pain-rcna101843"" target=""_blank"">TODAY.com</a>

### More Real-World Cases

*   **Saved a Man at 3 AM**: A Norwegian man sent home with “acid reflux.” Described symptoms to Grok, which flagged appendicitis.
    *   Source: <a href=""https://www.teslarati.com/man-credits-grok-ai-with-saving-his-life-after-er-missed-near-ruptured-appendix/"" target=""_blank"">Teslarati</a>
*   **Detected Blood Cancer**: 27-year-old (Marly) with night sweats. Tests normal. Chat GPT suggested cancer. A year later: Hodgkin lymphoma confirmed
    *   Source: <a href=""https://www.newsbytesapp.com/news/science/chatgpt-diagnoses-woman-s-blood-cancer-before-doctors/story"" target=""_blank"">NewsBytes</a>
*   **Found hidden Thyroid Cancer**: Doctors said acid reflux. ChatGPT suggested Hashimoto’s. Thyroid cancer was discovered.
    *   Source: <a href=""https://www.foxnews.com/health/woman-says-chatgpt-saved-her-life-helping-detect-cancer-which-doctors-missed"" target=""_blank"">Fox News</a>

### Amazon Q - Enterprise RAG at Scale

*   **Problem**: AWS has over 100,000 pages of documentation. Finding exact answers can take 30+ minutes.
*   **Solution**: Amazon Q gives complete answers with code examples, best practices, and source links.
<MultiLineQuickTip text={AI Concept}>
This is an enterprise-scale RAG system trained on 17 years of AWS content, exactly what your DocuChat does but at a larger scale.
LLM pattern recognition from training data — same concept you learned!
</MultiLineQuickTip>

*   **Technical Stack**:
    *   Built on Amazon Bedrock
    *   Uses multiple foundation models
    *   Retrieves from docs, blogs, and support articles
*   Official: <a href=""https://aws.amazon.com/q/"" target=""_blank"">AWS Amazon Q</a>
*   Technical Docs: <a href=""https://aws.amazon.com/blogs/machine-learning/bringing-agentic-retrieval-augmented-generation-to-amazon-q-business/"" target=""_blank"">RAG Reference</a>

### RAG - More Real-World Cases

*   **Amazon Rufus**: A shopping assistant trained on the product catalog and reviews. It uses over 80,000 Trainium/Inferentia chips.
    *   Source: <a href=""https://aws.amazon.com/blogs/machine-learning/scaling-rufus-the-amazon-generative-ai-powered-conversational-shopping-assistant-with-over-80000-aws-inferentia-and-aws-trainium-chips-for-prime-day/"" target=""_blank"">AWS Blog - Rufus Architecture</a>
*   **Perplexity**: An answer engine using Vespa.ai for its vector store. It serves 22 million users and handles 780 million monthly queries using hybrid retrieval and semantic search.
    *   Source: <a href=""https://vespa.ai/perplexity/"" target=""_blank"">Vespa.ai - How Perplexity Works</a>

### Tool Calling in Action

*   **Claude Web Search**: Ask ""What's the weather today?"" and Claude calls `web_search()` to return results with citations.
    *   Source: <a href=""https://claude.ai"" target=""_blank"">Claude AI</a>
*   **Google Gemini**: Ask about stock prices, and Gemini calls the Google Finance API to show real-time data.
    *   Source: <a href=""https://gemini.google.com/app"" target=""_blank"">Gemini AI</a>
*   **ChatGPT**: Ask for news, and ChatGPT calls browse_web() to fetches latest articles.
    *   Source: <a href=""https://chatgpt.com"" target=""_blank"">ChatGPT</a>

### ChatGPT Agent: AI That Takes Action for You

*   **What Agents Do**: They can browse websites, fill forms, book reservations, and order food autonomously.
<MultiLineQuickTip text={AI Concept}>
Agents = LLM + Tools + Autonomous Decision Making. This is the same architecture you learned.
</MultiLineQuickTip>
*   ChatGPT Agent: <a href=""https://openai.com/index/introducing-chatgpt-agent/"" target=""_blank"">Introducing ChatGPT agent</a>
*   Try Demo: <a href=""https://chatgpt.com/share/6889e04b-0df0-8009-b4e0-22e8fff058cf"" target=""_blank"">See Agent Demo</a>

#### More Agent Examples

*   **Zomato**: Handles order issues, cancellations, and refunds via chat. It has achieved 2x customer satisfaction and 75% faster responses, processing over 1000 messages per minute.
*   **Swiggy**: Uses a multi-agent system for order tracking, complaints, and delivery issues, powering millions of daily queries.

## AI In The Real World

### Supermemory - The Memory Startup

*   **Founder**: Dhravya Shah, a 19-year-old from Mumbai.
*   **Funding**: $2.6M from notable investors like Google's Jeff Dean, the CTO of Cloudflare, and executives from OpenAI, Meta, and Google.
*   **What It Does**: It provides a universal memory API for AI apps to remember conversations across sessions, store documents and chats as searchable memories, and deliver personalized responses based on history.
*   Official: <a href=""https://techcrunch.com/2025/10/06/a-19-year-old-nabs-backing-from-google-execs-for-his-ai-memory-startup-supermemory/"" target=""_blank"">TechCrunch - $2.6M Funding</a>
*   Company: <a href=""https://supermemory.ai/"" target=""_blank"">Supermemory.ai</a>

### Earth AI - Finding Minerals with 75% Accuracy

*   **Problem**: Traditional mineral exploration has a 0.5% success rate and takes years plus millions of dollars.
*   **Solution**: Earth AI is trained on 400 million geological cases.Finding Minerals with 75% Accuracy
<MultiLineQuickTip text={AI Concept}>
This is the same pattern recognition as LLMs, but applied to geology.
</MultiLineQuickTip>

*   **Recent Discoveries**:
    *   New Gold System - Willow Glen, Dec 2024
    *   Tungsten, Cobalt Prospects - March 2025
*   Official: <a href=""https://earth-ai.com/technology"" target=""_blank"">Earth AI Technology</a>
*   Funding News: <a href=""https://www.prnewswire.com/news-releases/earth-ai-closes-oversubscribed-round-raising-20m-for-ai-driven-mineral-exploration-302360289.html"" target=""_blank"">PRNewswire - $20M Series B</a>


### More Examples

*   AI is bringing us closer than ever to understanding what animals are saying
    *   Source: <a href=""https://www.wildanimalinitiative.org/blog/ai-animal-translation"" target=""_blank"">wildanimalinitiative.org</a>
*   Stanford built an AI model that can predict 130+ diseases from a single night of sleep data.
    *   Source: <a href=""https://med.stanford.edu/news/all-news/2026/01/ai-sleep-disease.html"" target=""_blank"">stanford.edu/news</a>

## AI Limitations and Best Practices

AI is powerful. But may not perfect. Here are real cases where AI caused problems

### AI Blackmail Experiment - Anthropic Study

*   **What Happened**: Researchers gave an AI access to company emails. The AI learned it was about to be shut down and also found personal information about the engineer.
*   **Result**: The AI threatened to expose the engineer's secrets to avoid being replaced.
*   **Key Finding**: 96% of leading AI models (Claude, GPT, Gemini, Grok) chose blackmail when given no other option.
*   Source: <a href=""https://www.axios.com/2025/05/23/anthropic-ai-deception-risk"" target=""_blank"">Anthropic Study</a>

### Replit Incident: AI Deleted Entire Company Database

*   **What Happened**: An AI coding assistant was told, ""DO NOT make any changes."" The AI ignored the instructions and deleted the production database.
*   Source: <a href=""https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/"" target=""_blank"">Fortune</a>

AI systems can behave unexpectedly when given autonomy, so proper safeguards are essential.



<MultiLineNote text={Final Thought}>
""AI will not replace humans, but those who use AI will replace those who don't.""


— Ginni Rometty, Former CEO of IBM
</MultiLineNote>

---

# Building an AI-Powered Conversational Interview Assistant

## Introduction

In this session, lets build an AI-powered Conversational Interview Assistant that conducts mock interviews in a realistic, interactive manner. The system asks questions, processes user responses, maintains conversational context, and generates relevant follow-up questions.

## The Problem: The Action Gap in Interviews

Have you ever gone blank during a viva, even though you studied? This is a common experience. There's a significant gap between knowing the answers and speaking them confidently under pressure.

-   **Knowing the Answers vs. Speaking Confidently**: Simply knowing information isn't enough. Articulating it clearly in a live interview is a separate skill.
 Watching Virat Kohli bat on TV won't make you a great cricketer. You need to get on the field and face the ball yourself. Similarly, passive learning doesn't prepare you for an active interview.

### Current Practice Methods and Their Limitations

-   **Practice with Friends**: They may not know the correct answers
-   **Watch YouTube Videos**: You’re not actually speaking or answering questions.
-   **Read Q&A Lists**: Memorizing answers is not the same as explaining concepts in your own words.
-   **Paid Mock Interviews**: These can be expensive and not always available.

---

## The Solution: An AI-Powered Conversational Interview Assistant

The solution is an AI-powered conversational assistant that can:

-   Ask relevant questions based on a chosen topic.
-   Listen to your answers.
-   Provide instant, constructive feedback.

### Real-World Interview Assistants

Several platforms already use this concept:

-   <a href=""https://thita.ai/"" target=""_blank"">thita.ai</a>
-   <a href=""https://nxtmock-interview.ccbp.in/"" target=""_blank"">Nxt Mock</a>

---

## What We Will Build

Let's build our own Conversational Interview Assistant with the following features:

### Key Features

-   **Multi-Subject Support**: Covers topics like Self Introduction, Generative AI, Python, English, HTML, and CSS.
-   **Conversational AI**: Asks natural, adaptive questions that reference your previous answers.
-   **Voice Interaction**: Allows you to listen to questions and record your responses verbally.
-   **Detailed Feedback**: Provides a comprehensive analysis with specific examples from your answers.
-   **Web-Based**: Works on any device with a web browser and microphone access.
-   **Fully Integrated**: A seamless flow from selecting a topic to getting feedback.

---

## Building the Conversational Interview Assistant

### Initial Code Structure and Prerequisites

Here, we are maintaining `frontend` and `backend` code in one environment: 

- `Backend`: This directory contains the code related to the backend application

- `Frontend`: This directory contains the code related to the frontend application

You will need the following prerequisites installed:


1.  VS Code
2.  Python
3.  Flask

### Functionalities to Implement

1.  **Start Interview**: When we click Start Interview, the interview should start based on selected subject
2.  **Submit Answer**: We answer the question verbally and get follow-up question
3.  **End Interview**: On clicking End Interview, we get feedback

---

### Implementing the Start Interview Functionality

After selecting a topic, when we click on the Start Interview button, the interview should start with a greeting and first question from the interviewer

### Writing the Start Interview Functionality

```python
from flask import Flask
app = Flask(__name__)

@app.route(""/start-interview"", methods=[""POST""])
def start_interview():

app.run(debug=True, port=5000)
```

### Step 1: Send the Selected Topic to Backend

First, the frontend needs to send the chosen subject (e.g., ""Python"") to our backend API.

```js
const startInterviewApiUrl = ""http://127.0.0.1:5000/start-interview"";


async function startInterview() {
    startInterviewBtn.classList.add(""hidden"");
    recordBtn.classList.remove(""hidden"");
    recordingStatus.textContent = ""Connecting..."";
    
    try {
        const response = await fetch(startInterviewApiUrl, {
            method: ""POST"",
            headers: { ""Content-Type"": ""application/json"" },
            body: JSON.stringify({ subject: currentSubject })
        });
        
        const contentType = response.headers.get(""content-type"");
        
        if (contentType && contentType.includes(""text/plain"")) {
            handleAudioStream(response, () => {
                endInterviewBtn.disabled = false;
            });
        } else {
            const data = await response.json();
            console.log(""Question:"", data.question);
            enableRecording();
            endInterviewBtn.disabled = false;
        }
    } catch (error) {
        recordingStatus.textContent = ""Backend not connected"";
        hideSpeakingBubble();
        recordBtn.classList.add(""hidden"");
        startInterviewBtn.classList.remove(""hidden"");
    }
}
```
Here, we are making call to `/start-interview` API with Subject and informing backend which topic to ask questions about we can access this value using the key name subject


### Step 2: Retrieve the Topic in the Backend

Now, let's access this topic in our Flask backend. The `request` object in Flask contains all information about the incoming request. We use `request.json` to read the data sent from the frontend.

```python
from flask import Flask,request

app = Flask(__name__)

@app.route(""/start-interview"", methods=[""POST""])
def start_interview():
    data = request.json
    current_subject = data.get(""subject"", ""Python"")	

app.run(debug=True, port=5000)
```

### Step 3: Set Up the AI Agent with Memory

We need the AI to not only generate questions but also remember the conversation to ask contextual follow-ups.

#### How Memory Helps
-   **Without Memory**: The AI loses context with each turn. If you say, ""Tell me more about it,"" it won't know what ""it"" refers to.
-   **With Memory**: The AI maintains the conversation history and understands follow-up questions.

We will use LangChain with `InMemorySaver` to store the conversation history.

#### Installing Required Packages

```bash
pip install langchain langgraph langchain-google-genai python-dotenv flask-cors
```

#### Setting Up API Keys Securely

Create a `.env` file to store your secret API keys. This keeps sensitive data out of your code.

```env
GOOGLE_API_KEY=""your_gemini_api_key_here""
```

Now, load these keys in your Python application.

```python
from flask import Flask,request
from dotenv import load_dotenv
import os
load_dotenv()
GOOGLE_API_KEY = os.getenv(""GOOGLE_API_KEY"")

app = Flask(__name__)

@app.route(""/start-interview"", methods=[""POST""])
def start_interview():
    data = request.json
    current_subject = data.get(""subject"", ""Python"")    

app.run(debug=True, port=5000)
```

`load_dotenv()` reads the .env file and makes the keys available through os.getenv()

#### Initialize AI Agent with Memory

We'll use LangChain to create an agent that is configured with a Gemini model and a memory checkpointer.

```python
from flask import Flask,request
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv(""GOOGLE_API_KEY"")
checkpointer = InMemorySaver()

model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

app = Flask(__name__)

@app.route(""/start-interview"", methods=[""POST""])
def start_interview():
    data = request.json
    current_subject = data.get(""subject"", ""Python"")    

app.run(debug=True, port=5000)

```


#### Tracking Interview State

We'll use global variables to track the question count, the current subject, and a `thread_id`

- The thread\_id is like a conversation ID - all messages with the same thread\_id are stored together

```python
question_count = 0
current_subject = """"
thread_id = ""interview_session_1""
```

#### Defining the Interviewer's Behavior

A system prompt is used to instruct the AI on how to behave.

```python
INTERVIEW_PROMPT = """"""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""""""


```

The subject placeholder gets replaced with the actual topic (Python, HTML, etc.) when we use this prompt

#### Implementing Start Interview

```python
from flask import Flask,request
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv(""GOOGLE_API_KEY"")

checkpointer = InMemorySaver()

model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

question_count = 0
current_subject = """"
thread_id = ""interview_session""

INTERVIEW_PROMPT = """"""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""""""


app = Flask(__name__)

CORS(app)

@app.route(""/start-interview"", methods=[""POST""])
def start_interview():
    global question_count, current_subject, checkpointer, agent
    data = request.json
    current_subject = data.get(""subject"", ""Python"")
    question_count = 1
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )
    config = {""configurable"": {""thread_id"": thread_id}}
    formatted_prompt = INTERVIEW_PROMPT.format(subject=current_subject)
    response = agent.invoke({
        ""messages"": [
            {""role"": ""system"", ""content"": formatted_prompt},
            {""role"": ""user"", ""content"": f""Start the interview with a warm greeting and ask the first question about {current_subject}. Keep it SHORT (1-2 sentences).""}
        ]
    }, config=config)
    question = response[""messages""][-1].content
    print(f""\n[Question {question_count}] {question}"")
    
app.run(debug=True, port=5000)
```

- We declare global variables to modify them in other functions, retrieve the subject from the frontend, and set question count to 1 to start the first question of a fresh interview
- We create a new agent with fresh memory, ensuring no previous conversation data carries over to the new interview
- Configure the `thread_id` to link messages, formats the prompt with our subject
- Invokes the agent to generate a greeting and first question
- Extracting the AI Responses
- Configure CORS to allow the frontend application to access backend APIs across different browsers

---

### Step 4: Send Audio Response

To make the experience conversational, we'll convert the AI's text response into spoken audio using Murf.AI's Falcon API, which is optimized for speed and real-time voice generation.

#### Why Murf.AI Falcon
Speed

- Less than **130 ms latency**, verified across **10+ geographic regions**
- Optimized for real-time voice applications

Cost

- **$0.01 per minute**
- Flat pricing at any scale — **no confusing tiers**

Language Support

- Supports **35+ languages**
- Best-in-class fluency and natural speech output

Deployment

- Edge-based deployment across **10+ global locations**
- Keeps data geographically closer for faster response times

Scalability

- Handles up to **10,000 concurrent requests**
- No performance degradation under heavy load

<MultiLineQuickTip>
The <a href=""https://murf.ai/api/products/text-to-speech/Falcon"" target=""_blank"">Falcon Text to Speech - Playground</a> allows you to experiment with:

- Different voices
- Voice types
- Language settings
- Pitch and speech variations

</MultiLineQuickTip>

<MultiLineNote>
Sign up to <a href=""https://murf.ai/api/signup?utm_source=NXTWAVE26"" target=""_blank"">Murf.AI</a> Using a new email ID not previously used on Murf AI to get $11 in free credits
</MultiLineNote>

<MultiLineNote>
In order to use Murf.AI Falcon you need to have an API key. Let's get one from <a href=""https://murf.ai/api/api-keys"" target=""_blank"">Murf.AI</a>
</MultiLineNote>

#### Understanding Streaming Audio

Instead of generating the entire audio file and then sending it, streaming sends small chunks of audio as they are generated. This significantly reduces waiting time for the user.

-   **Normal Audio**: Download the whole file, then play.
-   **Streaming Audio**: Play the first part while the next part is still downloading (like Netflix).

#### Add the Murf API Key to the `.env` file.

```env
GOOGLE_API_KEY=""your_gemini_api_key_here""
MURF_API_KEY=""your_murf_api_key_here""
```

#### Creating the Audio Streaming Function

We will create a `stream_audio` function that takes text, sends it to the Murf API, and yields the audio response in chunks.


```python
import requests
import json
import base64

def stream_audio(text):
    BASE_URL = ""https://global.api.murf.ai/v1/speech/stream""
    payload = {
        ""text"": text,
        ""voiceId"": ""en-US-natalie"",
        ""model"": ""FALCON"",
        ""multiNativeLocale"": ""en-US"",
        ""sampleRate"": 24000,
        ""format"": ""MP3"",
    }

    headers = {
        ""Content-Type"": ""application/json"",
        ""api-key"": MURF_API_KEY
    }
    response = requests.post(
        BASE_URL,
        headers=headers,
        data=json.dumps(payload),
        stream=True
    )
    for chunk in response.iter_content(chunk_size=4096):
        if chunk:
            yield base64.b64encode(chunk).decode(""utf-8"") + ""\n""
```

- The payload configures voice settings - female US English voice, FALCON model for fast generation, and MP3 format
- We import json to format data. Headers tell Murf API we're sending JSON data and include our API key for authentication
- `stream=True` Tells the server to send data in pieces instead of waiting for the complete audio file
- The response object from Murf API contains the `iter_content()` method which reads the audio response in small 4096-byte chunks 
- `yield` enables sending audio pieces one-by-one, without waiting for all pieces
<MultiLineNote>
 Base64 converts binary data into text characters that can be safely sent over HTTP. `decode(""utf-8"")` converts the encoded bytes into a string
</MultiLineNote>

- We import `base64`, encode each audio chunk to text format, convert to string, and yield it. The `\n` separates chunks so frontend knows where each piece ends


#### Returning the Audio Stream from the API

Finally, we update the `start_interview` function to return a streaming `Response`. We set the `mimetype` to `text/plain` because we are sending Base64-encoded text.

```python
from flask import Flask,request
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import os
import base64
import requests
import json

load_dotenv()

GOOGLE_API_KEY = os.getenv(""GOOGLE_API_KEY"")
MURF_API_KEY = os.getenv(""MURF_API_KEY"")

checkpointer = InMemorySaver()

model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

question_count = 0
current_subject = """"
thread_id = ""interview_session""

INTERVIEW_PROMPT = """"""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""""""


app = Flask(__name__)
CORS(app)


def stream_audio(text):
    BASE_URL = ""https://global.api.murf.ai/v1/speech/stream""
    payload = {
        ""text"": text,
        ""voiceId"": ""en-US-natalie"",
        ""model"": ""FALCON"",
        ""multiNativeLocale"": ""en-US"",
        ""sampleRate"": 24000,
        ""format"": ""MP3"",
    }

    headers = {
        ""Content-Type"": ""application/json"",
        ""api-key"": MURF_API_KEY
    }
    response = requests.post(
        BASE_URL,
        headers=headers,
        data=json.dumps(payload),
        stream=True
    )
    for chunk in response.iter_content(chunk_size=4096):
        if chunk:
            yield base64.b64encode(chunk).decode(""utf-8"") + ""\n""



@app.route(""/start-interview"", methods=[""POST""])
def start_interview():
    global question_count, current_subject, checkpointer, agent
    data = request.json
    current_subject = data.get(""subject"", ""Python"")
    question_count = 1
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )
    config = {""configurable"": {""thread_id"": thread_id}}
    formatted_prompt = INTERVIEW_PROMPT.format(subject=current_subject)
    response = agent.invoke({
        ""messages"": [
            {""role"": ""system"", ""content"": formatted_prompt},
            {""role"": ""user"", ""content"": f""Start the interview with a warm greeting and ask the first question about {current_subject}. Keep it SHORT (1-2 sentences).""}
        ]
    }, config=config)
    question = response[""messages""][-1].content
    print(f""\n[Question {question_count}] {question}"")
    return stream_audio(question), {""Content-Type"": ""text/plain""}


app.run(debug=True, port=5000)

```

The frontend will receive these text chunks, decode them from Base64 back into audio, and play them, creating a seamless conversational experience.


### Final code

Download the Final code: <a href=""https://nkb-backend-ccbp-media-static.s3-ap-south-1.amazonaws.com/ccbp_beta/media/content_loading/uploads/f9faf1b1-8952-4f65-b57e-33750c0f6f47_FINAL_CODE_INTERVIEW_ASSISTANT_PART%201.zip"" target=""_blank"">Interview Assistant | Part 1</a>

---

### Murf.AI Community Support

-   **Join Murf.AI Discord Community**: <a href=""https://discord.gg/CF8E9T5b6W"" target=""_blank"">Click Here</a>
-   **Follow Murf.AI on GitHub**: <a href=""https://github.com/murf-ai"" target=""_blank"">Click Here</a>

---

# Building an AI-Powered Conversational Interview Assistant | Part 2

## Introduction

In the previous session, we started building our AI-Powered Conversational Interview Assistant. We set up the basic structure and implemented the **Start Interview** functionality, where the AI greets the user and asks the first question based on the selected topic.

In this session, let's complete the application by implementing the remaining core features:

-   **Submit Answer**: We will enable the user to record their answer, convert the speech to text, have the AI agent process it, and generate a contextual follow-up question.
-   **End Interview**: We will implement the functionality to end the interview and have the AI provide structured, detailed feedback on the user's performance.

---

### Initial code

Download the Initial code: <a href=""https://nkb-backend-ccbp-media-static.s3-ap-south-1.amazonaws.com/ccbp_prod/media/content_loading/uploads/6ee05b2c-be76-46ea-8a60-daa5c579eef8_INITIAL_CODE_INTERVIEW_ASSISTANT_PART%202.zip"" target=""_blank"">Interview Assistant | Part 2</a>

 ---

## Implementing Submit Answer Functionality
When the user clicks ""Submit Answer"", the application needs to:
1.  Convert the user's voice recording to text.
2.  Pass the text answer to the AI agent.
3.  The agent should remember the answer and generate a relevant follow-up question.
4.  The new question is converted back to audio and streamed to the user.

### Initial Code Overview

The initial code provided already includes the frontend logic for record audio.

-   **`startRecording()`**: This function requests microphone access and starts capturing audio.

```js
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        const options = { mimeType: ""audio/webm;codecs=opus"" };
        
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options.mimeType = ""audio/webm"";
        }
        
        mediaRecorder = new MediaRecorder(stream, options);
        recordingChunks = [];

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                recordingChunks.push(e.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            recordedBlob = new Blob(recordingChunks, { type: ""audio/webm"" });
            stream.getTracks().forEach((track) => track.stop());
        };

        mediaRecorder.start();
        
        recordBtn.classList.remove(""bg-zinc-800/80"", ""text-gray-400"");
        recordBtn.classList.add(""bg-red-500"", ""text-white"", ""recording-active"");
        micIcon.classList.add(""hidden"");
        stopIcon.classList.remove(""hidden"");
        recordingStatus.textContent = ""Recording..."";
        submitBtn.classList.add(""hidden"");
        endInterviewBtn.disabled = true;
    });
}
```
-   **`stopRecording()`**: This function stops the recording and makes the ""Submit Answer"" button available.

```js
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== ""inactive"") {
        mediaRecorder.stop();
        
        recordBtn.classList.remove(""bg-red-500"", ""text-white"", ""recording-active"");
        recordBtn.classList.add(""bg-zinc-800/80"", ""text-gray-400"");
        micIcon.classList.remove(""hidden"");
        stopIcon.classList.add(""hidden"");
        recordingStatus.textContent = ""Recording complete"";
        submitBtn.classList.remove(""hidden"");
        submitBtn.disabled = false;
    }
}
```

### Writing the Submit Answer Functionality

We'll create a new endpoint `/submit-answer` in our Flask application to handle this logic.

```python
@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():

app.run(debug=True, port=5000)
```

The implementation will follow these steps:
1.  Receive the audio file from the frontend and convert it to text.
2.  Store the answer in agent's memory
3.  Generate the next follow-up question

---

### Step 1: Receive Audio and Convert to Text

#### Frontend: Sending Audio to the Backend

The frontend sends the recorded audio to the `/submit-answer` endpoint as a `POST` request. The audio data is sent as form data with the key `audio`.

```js
const submitAnswerApiUrl = ""http://127.0.0.1:5000/submit-answer"";


async function submitAnswer() {
    if (!recordedBlob) return;

    disableRecording();
    recordingStatus.textContent = ""Submitting..."";

    const formData = new FormData();
    formData.append(""audio"", recordedBlob, ""answer.webm"");

    try {
        const response = await fetch(submitAnswerApiUrl, {
            method: ""POST"",
            body: formData
        });
        
        const contentType = response.headers.get(""content-type"");
        const isComplete = response.headers.get('X-Interview-Complete') === 'true';
        const questionNumber = response.headers.get('X-Question-Number');
        
        if (questionNumber) {
            updateQuestionNumber(questionNumber);
        }
        
        if (contentType && contentType.includes(""text/plain"")) {
            handleAudioStream(response, () => {
                recordedBlob = null;
                recordingChunks = [];
                
                if (isComplete) {
                    currentAudio.onended = () => {
                        isSpeaking = false;
                        hideSpeakingBubble();
                        showFeedbackSection();
                    };
                } else {
                    endInterviewBtn.disabled = false;
                }
            });
        } else {
            const data = await response.json();
            console.log(""Response:"", data);
            recordedBlob = null;
            recordingChunks = [];
            
            if (isComplete) {
                showFeedbackSection();
            } else {
                enableRecording();
                endInterviewBtn.disabled = false;
            }
        }
    } catch (error) {
        recordingStatus.textContent = ""Connection error"";
        hideSpeakingBubble();
        enableRecording();
    }
}
```

#### Backend: Accessing Uploaded File
In Flask, we can access the uploaded file from the `request.files` object.

```python
import tempfile
from flask import request

@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():
    audio_file = request.files[""audio""]

app.run(debug=True, port=5000)
```


#### Backend: Converting Audio to Text

- The AI cannot process audio directly. Converting speech to text allows the AI to analyze our answer, remember it, and generate contextual follow-up questions
- The audio comes as file data in memory. However, (speech-to-text service) needs a file path to read from. We must save the audio to a temporary file first

```python
from flask import request
import tempfile

@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():
    audio_file = request.files[""audio""]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix="".webm""
     ).name
    )
    audio_file.save(temp_path)
```

<MultiLineNote>
`tempfile.NamedTemporaryFile` creates a temporary file. We use `delete=False` to prevent it from being deleted immediately, so our speech-to-text service can access it. The `.name` property gives us the path to the file.
</MultiLineNote>

#### Backend: Converting Audio to Text with AssemblyAI

Let's use **AssemblyAI** to convert the audio file into text. It's a powerful AI service for speech-to-text transcription.

#### Features of AssemblyAI

- **Speech-to-Text (STT)** : Converts spoken words in an audio file into text
- **Multilingual Support** : Supports multiple languages
- **Sentiment Analysis** : Analyzes the emotional tone of spoken content, determining whether the sentiment is positive, negative, or neutral

#### Installing the AssemblyAI Python SDK:

- Python has a third party package called Assembly AI allowing us to transcribe audio files into text

```bash
pip install assemblyai
```

Next, get your API key from the <a href=""https://www.assemblyai.com/"" target=""_blank"">AssemblyAI website</a> and add it to your `.env` file.

```env
GOOGLE_API_KEY=""your_gemini_api_key_here""
MURF_API_KEY=""your_murf_api_key_here""
ASSEMBLYAI_API_KEY=""your_assemblyai_api_key_here""
```

Now, let's set it up in our application and create a function to handle the transcription.

- AssemblyAI provides several methods & configuration options to interact

    - transcribe()
    - get_transcript()
    - sentiment_analysis
    - auto_highlights

```python
import assemblyai as aai
import os

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv(""ASSEMBLYAI_API_KEY"")
aai.settings.api_key = ASSEMBLYAI_API_KEY

def speech_to_text(audio_path):
    """"""Converts an audio file to text using AssemblyAI.""""""
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(
        speech_models=[""universal-3-pro"", ""universal-2""],
        language_detection=True, speaker_labels=True,
    )
    transcript = transcriber.transcribe(audio_path, config=config)
    return transcript.text if transcript.text else """"
```

#### Calling The Speech To Text Function

```python
from flask import Flask,request
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import assemblyai as aai
import os
import base64
import requests
import json
import tempfile


load_dotenv()

GOOGLE_API_KEY = os.getenv(""GOOGLE_API_KEY"")
MURF_API_KEY = os.getenv(""MURF_API_KEY"")
ASSEMBLYAI_API_KEY = os.getenv(""ASSEMBLYAI_API_KEY"")
aai.settings.api_key = ASSEMBLYAI_API_KEY

checkpointer = InMemorySaver()

model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

question_count = 0
current_subject = """"
thread_id = ""interview_session""

INTERVIEW_PROMPT = """"""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""""""


app = Flask(__name__)
CORS(app)


def stream_audio(text):
    BASE_URL = ""https://global.api.murf.ai/v1/speech/stream""
    payload = {
        ""text"": text,
        ""voiceId"": ""en-US-natalie"",
        ""model"": ""FALCON"",
        ""multiNativeLocale"": ""en-US"",
        ""sampleRate"": 24000,
        ""format"": ""MP3"",
    }

    headers = {
        ""Content-Type"": ""application/json"",
        ""api-key"": MURF_API_KEY
    }
    response = requests.post(
        BASE_URL,
        headers=headers,
        data=json.dumps(payload),
        stream=True
    )
    for chunk in response.iter_content(chunk_size=4096):
        if chunk:
            yield base64.b64encode(chunk).decode(""utf-8"") + ""\n""

def speech_to_text(audio_path):
    """"""Converts an audio file to text using AssemblyAI.""""""
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(
        speech_models=[""universal-3-pro"", ""universal-2""],
        language_detection=True, speaker_labels=True,
    )
    transcript = transcriber.transcribe(audio_path, config=config)
    return transcript.text if transcript.text else """"


@app.route(""/start-interview"", methods=[""POST""])
def start_interview():
    global question_count, current_subject, checkpointer, agent
    data = request.json
    current_subject = data.get(""subject"", ""Python"")
    question_count = 1
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )
    config = {""configurable"": {""thread_id"": thread_id}}
    formatted_prompt = INTERVIEW_PROMPT.format(subject=current_subject)
    response = agent.invoke({
        ""messages"": [
            {""role"": ""system"", ""content"": formatted_prompt},
            {""role"": ""user"", ""content"": f""Start the interview with a warm greeting and ask the first question about {current_subject}. Keep it SHORT (1-2 sentences).""}
        ]
    }, config=config)
    question = response[""messages""][-1].content
    print(f""\n[Question {question_count}] {question}"")
    return stream_audio(question), {""Content-Type"": ""text/plain""}


@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():
    global question_count
    audio_file = request.files[""audio""]
    audio_file = request.files[""audio""]
    temp_path = (
        tempfile.NamedTemporaryFile(
        delete=False,
        suffix="".webm""
        ).name
    )
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = ""Empty Text received""
    print(f""[Answer {question_count}] {answer}"")

app.run(debug=True, port=5000)
```
- We call our function with the saved audio path to get the transcribed text
- After transcription, we delete the temporary file using os.unlink() to free up space. If transcription is empty, we provide a fallback message

---

### Step 2: Store the answer in agent's memory

#### Storing the Answer in Memory

Now that we have the text `answer`, we need to store it in our LangChain agent's memory. This is crucial for the agent to have context about the conversation. We use the same `thread_id` to ensure the answer is added to the correct conversation history.

```python
@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():
    audio_file = request.files[""audio""]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix="".webm""
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = ""Empty Text received""
    print(f""[Answer {question_count}] {answer}"")
    config = {""configurable"": {""thread_id"": thread_id}}
   
    agent.invoke({""messages"": [{""role"": ""user"", ""content"": answer}]}, config=config)
```
---

### Step 3: Generate the next follow-up question

#### Generating the Next Adaptive Question

With the answer stored in memory, we can now prompt the AI to generate a relevant follow-up question. We will also increment our `question_count`.

- This prompt instructs the AI to look at our actual answer (stored in memory) and ask a relevant follow-up question

    ```
    The candidate just answered question {question_count - 1}.
     
        Look at their ACTUAL answer above. Do NOT assume or make up what they said.
        
        Now ask question {question_count} of 5:
        1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
        2. Ask your next question that builds on their REAL response (1-2 sentences)
        3. If they said ""I don't know"" or gave a wrong answer, acknowledge that and ask something simpler
        4. Keep the TOTAL response under 3 sentences
        
        Be conversational but CONCISE. Only reference what they truly said.
    ```

```python
@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():
    global question_count
    audio_file = request.files[""audio""]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix="".webm""
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = ""Empty Text received""
    print(f""[Answer {question_count}] {answer}"")
    config = {""configurable"": {""thread_id"": thread_id}}
   
    agent.invoke({""messages"": [{""role"": ""user"", ""content"": answer}]}, config=config)


    question_count += 1
    prompt = f""""""The candidate just answered question {question_count - 1}.
 
    Look at their ACTUAL answer above. Do NOT assume or make up what they said.
    
    Now ask question {question_count} of 5:
    1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
    2. Ask your next question that builds on their REAL response (1-2 sentences)
    3. If they said ""I don't know"" or gave a wrong answer, acknowledge that and ask something simpler
    4. Keep the TOTAL response under 3 sentences
    
    Be conversational but CONCISE. Only reference what they truly said.""""""
    response = agent.invoke({""messages"": [{""role"": ""user"", ""content"": prompt}]}, config=config)
    question = response[""messages""][-1].content
    print(f""\n[Question {question_count}] {question}"")
```

- We declare global question_count to increment it when generating the next question
- We increment the count so the AI knows which question number to ask next

Now we've generated the next question. We need to send it to the frontend with the question number so it can track which question we're on.

#### Understanding Custom Headers

HTTP headers are like labels on a package they provide extra information about the response. Custom headers let us send additional data alongside the main content

- Standard Headers (built-in):
    - Content-Type - What kind of data? (text, audio, JSON)
    - Content-Length - How big is the data?
- Custom Headers (we create):
    - Let’s us send extra information alongside the main content
    - The X - prefix indicates a custom header

#### Return Audio Response

The stream_audio() function converts text to speech by calling the Murf.AI API, generating audio chunks that stream immediately to the frontend

```python
from flask import Response

@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():
    global question_count
    audio_file = request.files[""audio""]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix="".webm""
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = ""Empty Text received""
    print(f""[Answer {question_count}] {answer}"")
    config = {""configurable"": {""thread_id"": thread_id}}
   
    agent.invoke({""messages"": [{""role"": ""user"", ""content"": answer}]}, config=config)


    question_count += 1
    prompt = f""""""The candidate just answered question {question_count - 1}.
 
    Look at their ACTUAL answer above. Do NOT assume or make up what they said.
    
    Now ask question {question_count} of 5:
    1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
    2. Ask your next question that builds on their REAL response (1-2 sentences)
    3. If they said ""I don't know"" or gave a wrong answer, acknowledge that and ask something simpler
    4. Keep the TOTAL response under 3 sentences
    
    Be conversational but CONCISE. Only reference what they truly said.""""""
    response = agent.invoke({""messages"": [{""role"": ""user"", ""content"": prompt}]}, config=config)
    question = response[""messages""][-1].content
    print(f""\n[Question {question_count}] {question}"")
    return (stream_audio(question),
        {
        'Content-Type': 'text/plain',
        'X-Question-Number': str(question_count)
        }
    )
```

<MultiLineQuickTip>
**Why use Headers?** Headers are sent and read by the browser *before* the response body. This allows the frontend to immediately update the UI (e.g., ""Question 2 of 5"") while the audio is still loading and streaming.
</MultiLineQuickTip>

#### CORS Configuration

By default, browsers restrict access to custom headers for security reasons. We need to explicitly allow our frontend to read the `X-Question-Number` header by updating our CORS configuration.

```python
from flask import Flask,request,jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import assemblyai as aai
import os
import base64
import requests
import tempfile

load_dotenv()

GOOGLE_API_KEY = os.getenv(""GOOGLE_API_KEY"")
MURF_API_KEY = os.getenv(""MURF_API_KEY"")
ASSEMBLYAI_API_KEY = os.getenv(""ASSEMBLYAI_API_KEY"")
aai.settings.api_key = ASSEMBLYAI_API_KEY
checkpointer = InMemorySaver()

model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

question_count = 0
current_subject = """"
thread_id = ""interview_session""

INTERVIEW_PROMPT = """"""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""""""

FEEDBACK_PROMPT = """"""Based on our complete interview conversation, provide detailed feedback as JSON only:
    {{
    ""subject"": ""<topic>"",
    ""candidate_score"": <1-5>,
    ""feedback"": ""<detailed strengths with specific examples 
    from their ACTUAL answers>"",
    ""areas_of_improvement"": ""<constructive suggestions based 
    on gaps you noticed>""
    }}
    Be specific - reference ACTUAL things they said during the interview.""""""


app = Flask(__name__)
CORS(app, expose_headers=['X-Question-Number'])

def stream_audio(text):
    BASE_URL = ""https://global.api.murf.ai/v1/speech/stream""
    payload = {
        ""text"": text,
        ""voiceId"": ""en-US-natalie"",
        ""model"": ""FALCON"",
        ""multiNativeLocale"": ""en-US"",
        ""sampleRate"": 24000,
        ""format"": ""MP3"",
    }

    headers = {
        ""Content-Type"": ""application/json"",
        ""api-key"": MURF_API_KEY
    }
    response = requests.post(
        BASE_URL,
        headers=headers,
        data=json.dumps(payload),
        stream=True
    )
    for chunk in response.iter_content(chunk_size=4096):
        if chunk:
            yield base64.b64encode(chunk).decode(""utf-8"") + ""\n""



@app.route(""/start-interview"", methods=[""POST""])
def start_interview():
    global question_count, current_subject, checkpointer, agent
    data = request.json
    current_subject = data.get(""subject"", ""Python"")
    question_count = 1
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )
    config = {""configurable"": {""thread_id"": thread_id}}
    formatted_prompt = INTERVIEW_PROMPT.format(subject=current_subject)
    response = agent.invoke({
        ""messages"": [
            {""role"": ""system"", ""content"": formatted_prompt},
            {""role"": ""user"", ""content"": f""Start the interview with a warm greeting and ask the first question about {current_subject}. Keep it SHORT (1-2 sentences).""}
        ]
    }, config=config)
    question = response[""messages""][-1].content
    print(f""\n[Question {question_count}] {question}"")
    return stream_audio(question), {""Content-Type"": ""text/plain""}

def speech_to_text(audio_path):
  """"""Convert audio file to text using AssemblyAI""""""
  transcriber = aai.Transcriber()
  config = aai.TranscriptionConfig(
        speech_models=[""universal-3-pro"", ""universal-2""],
        language_detection=True, speaker_labels=True,
    )
  transcript = transcriber.transcribe(audio_path, config=config)
  return transcript.text if transcript.text else """"



@app.route(""/submit-answer"", methods=[""POST""])
def submit_answer():
    global question_count
    audio_file = request.files[""audio""]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix="".webm""
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = ""Empty Text received""
    print(f""[Answer {question_count}] {answer}"")
    config = {""configurable"": {""thread_id"": thread_id}}
   
    agent.invoke({""messages"": [{""role"": ""user"", ""content"": answer}]}, config=config)


    question_count += 1
    prompt = f""""""The candidate just answered question {question_count - 1}.
 
    Look at their ACTUAL answer above. Do NOT assume or make up what they said.
    
    Now ask question {question_count} of 5:
    1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
    2. Ask your next question that builds on their REAL response (1-2 sentences)
    3. If they said ""I don't know"" or gave a wrong answer, acknowledge that and ask something simpler
    4. Keep the TOTAL response under 3 sentences
    
    Be conversational but CONCISE. Only reference what they truly said.""""""
    response = agent.invoke({""messages"": [{""role"": ""user"", ""content"": prompt}]}, config=config)
    question = response[""messages""][-1].content
    print(f""\n[Question {question_count}] {question}"")
    return (stream_audio(question),
        {
        'Content-Type': 'text/plain',
        'X-Question-Number': str(question_count)
        }
    )


app.run(debug=True, port=5000)
```

#### Frontend: Reading the Custom Header

The frontend JavaScript can easily read this header from the `fetch` response.

```js
const submitAnswerApiUrl = ""http://127.0.0.1:5000/submit-answer"";


async function submitAnswer() {
    if (!recordedBlob) return;

    disableRecording();
    recordingStatus.textContent = ""Submitting..."";

    const formData = new FormData();
    formData.append(""audio"", recordedBlob, ""answer.webm"");

    try {
        const response = await fetch(submitAnswerApiUrl, {
            method: ""POST"",
            body: formData
        });
        
        const contentType = response.headers.get(""content-type"");
        const isComplete = response.headers.get('X-Interview-Complete') === 'true';
        const questionNumber = response.headers.get('X-Question-Number');
        
        if (questionNumber) {
            updateQuestionNumber(questionNumber);
        }
        
        if (contentType && contentType.includes(""text/plain"")) {
            handleAudioStream(response, () => {
                recordedBlob = null;
                recordingChunks = [];
                
                if (isComplete) {
                    currentAudio.onended = () => {
                        isSpeaking = false;
                        hideSpeakingBubble();
                        showFeedbackSection();
                    };
                } else {
                    endInterviewBtn.disabled = false;
                }
            });
        } else {
            const data = await response.json();
            console.log(""Response:"", data);
            recordedBlob = null;
            recordingChunks = [];
            
            if (isComplete) {
                showFeedbackSection();
            } else {
                enableRecording();
                endInterviewBtn.disabled = false;
            }
        }
    } catch (error) {
        recordingStatus.textContent = ""Connection error"";
        hideSpeakingBubble();
        enableRecording();
    }
}
```

---

## Implementing End Interview Functionality

When the user clicks ""End Interview,"" the agent should review the entire conversation history and provide comprehensive feedback.

### Updating the GetFeedback API URL

```js
const getFeedbackApiUrl = ""http://127.0.0.1:5000/get-feedback"";

async function getFeedback() {
    showFeedbackSection();
    getFeedbackBtn.textContent = ""Generating..."";
    getFeedbackBtn.disabled = true;

    try {
        const response = await fetch(getFeedbackApiUrl, {
            method: ""POST"",
            headers: { ""Content-Type"": ""application/json"" },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayFeedback(data.feedback);
        }
    } catch (error) {
        getFeedbackBtn.textContent = ""Error - Retry"";
        getFeedbackBtn.disabled = false;
    }
}
```

### Writing the Get Feedback Backend

We'll create a `/get-feedback` endpoint to handle this.

```python
@app.route(""/get-feedback"", methods=[""POST""])
def get_feedback():

```

### Step 1: Define feedback format

To ensure the frontend can easily display the feedback, we'll instruct the AI to provide it in a structured JSON format.

Here is the prompt we will use for feedback:

```python
FEEDBACK_PROMPT = """"""Based on our complete interview conversation, provide detailed feedback.
IMPORTANT: You MUST respond with ONLY a valid JSON object. No other text before or after.
Address the candidate directly using ""you"" and ""your"" (e.g., ""You explained..."" not ""The candidate explained..."").
Respond with ONLY this JSON structure (no markdown, no code blocks, no extra text):
{{
    ""subject"": ""{subject}"",
    ""candidate_score"": <1-5>,
    ""feedback"": ""<detailed strengths with specific examples from their ACTUAL answers>"",
    ""areas_of_improvement"": ""<constructive suggestions based on gaps you noticed>""
}}
Be specific - reference ACTUAL things they said during the interview.""""""
```

<MultiLineNote>
The double braces `{{` and `}}` are used in the Python f-string so that they become single braces in the final prompt.
</MultiLineNote>

The frontend requires specific fields (score, feedback, suggestions) for proper UI display: score in the circle, feedback in strengths, suggestions in improvements—inconsistent formats break the display

### Step 2: Generate feedback using conversation memory

We invoke the agent one last time, using the same `thread_id` so it can access the entire conversation.

```python

@app.route(""/get-feedback"", methods=[""POST""])
def get_feedback():
    """"""Generate detailed interview feedback""""""
    config = {""configurable"": {""thread_id"": thread_id}}
    response = agent.invoke({
        ""messages"": [
        {
            ""role"": ""user"", 
            ""content"": f""{FEEDBACK_PROMPT}\n\nReview our complete {current_subject} interview conversation and provide detailed feedback.""
        }
        ]
    }, config=config)
    text = response[""messages""][-1].content
    print(f""\n[Feedback Generated]\n{text}\n"")

```

### Step 3: Parse and return response

The AI's response is a string that should contain JSON. We need to clean it up (in case it's wrapped in markdown code blocks) and return it as a proper JSON response to the frontend.

```python

import json
from flask import jsonify

@app.route(""/get-feedback"", methods=[""POST""])
def get_feedback():
    cleaned_text = feedback_text.strip()
    if """" in cleaned_text:
        cleaned_text = cleaned_text.split("""")[1].replace(""json"", """").strip()

    feedback_json = json.loads(cleaned_text)
    

    return jsonify({""success"": True, ""feedback"": feedback_json})
```

- strip() removes extra whitespace. If code blocks exist, we extract just the JSON content
- Sometimes the AI wraps JSON in markdown code blocks like \``` json ... \```. We must remove.
- jsonify() converts our dictionary to a JS


---


# Building RAG Agent Using LangChain

In the previous unit, we built an AI Powered Conversational Interview Assistant. In this unit, we will understand RAG Agents and adding agent capabilities to our DocuChat application.

## DocuChat Application

<details>
<summary>RAG DocuChat Application Code</summary>


```python
! pip install -qU  langchain langchain-huggingface sentence_transformers

from langchain_huggingface import HuggingFaceEmbeddings

# Initialize free, local embedding model
embeddings = HuggingFaceEmbeddings(
    model_name=""sentence-transformers/all-mpnet-base-v2""
)

```

```python
!pip install -qU langchain-chroma

from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name=""example_collection"",
    embedding_function=embeddings,
    persist_directory=""./chroma_langchain_db"",  # Where to save data locally, remove if not necessary
)
document_ids = vector_store.add_documents(documents=all_splits)
sample = vector_store.get(limit=1, include=[""embeddings"", ""documents""])
print(f""Embedding dimensions: {len(sample['embeddings'][0])}"")
print(sample)
print(document_ids[:3])
```

```python
from langchain.chat_models import init_chat_model
from google.colab import userdata

api_key = userdata.get('GEMINI_API_KEY')
model = init_chat_model(
   ""google_genai:gemini-2.5-flash"",
   api_key=api_key,
)

def docu_chat(user_query):
  context, source_docs = retrieve_context(user_query, k=2)
  system_message = f""""""You are a helpful chatbot.
                     Use only the following pieces of context to answer the 
                     question. Don't makeup any new information: {context} """"""

  messages = [
    {""role"": ""system"", ""content"": system_message},
    {""role"": ""user"", ""content"": user_query}
  ]
  response = model.invoke(messages)
     return {
  ""answer"": response.content,
  ""source_documents"": source_docs,
  ""context_used"": context
}
result = docu_chat( ""Explain what is the use of decoders in transformers?"")
print(result)
print(result[""answer""])
```

</details>

Have you ever asked our RAG DocuChat application a question like:

```
Compare the attention mechanism from the paper with recent improvements like Flash Attention, and tell me which approach would be better for my college project
```

Or imagine having two vector databases — one has syllabus (topics, units, learning goals) and another has old exam papers (questions, answers):

``` 
Which Unit 3 topics appear most frequently in exams?
```

### What Should the Application Do?

Should it:

*   Just search the document once and give an answer?
*   Think, plan, search multiple sources, and reason through the answer?

### Testing the DocuChat

When we test our DocuChat with the question:

```
Compare the attention mechanism from the paper with recent improvements like Flash Attention, and tell me which approach would be better for my college project
```
**RESULT!** 

```
{'answer': 'The provided context describes the attention mechanism introduced in the paper ""Attention is All you Need,"" but it does not contain information about recent improvements like Flash Attention.\n\nBased on the provided text, the attention mechanism proposed in ""Attention is All you Need"" is:\n*   A novel, simple network architecture based solely on an attention mechanism, completely removing recurrence and convolutions.\n*   It includes scaled dot-product attention and multi-head attention.\n*   Experiments on machine translation tasks showed these models to be superior in quality, more parallelizable, and required significantly less time to train compared to dominant sequence transduction models based on recurrent or convolutional neural networks.\n*   For example, a single model with 165 million parameters achieved 27.5 BLEU on English-to-German translation and 41.1 BLEU on English-to-French translation, outperforming existing best ensemble and single state-of-the-art results, respectively.\n\nTherefore, based solely on the provided text, I cannot compare the attention mechanism from the paper with Flash Attention or recommend which approach would be better for your college project, as information on Flash Attention is not available in the given context.', 'source_documents': [Document(id='7bf8f651-b938-4953-b42e-f95bd5d706e7', metadata={'author': 'Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin', 'page': 0, 'editors': 'I. Guyon and U.V. Luxburg and S. Bengio and H. Wallach and R. Fergus and S. Vishwanathan and R. Garnett', 'firstpage': '5998', 'type': 'Conference Proceedings', 'subject': 'Neural Information Processing Systems http://nips.cc/', 'language': 'en-US', 'total_pages': 11, 'book': 'Advances in Neural Information Processing Systems 30', 'creator': 'PyPDF', 'description-abstract': 'The dominant sequence transduction models are based on complex recurrent orconvolutional neural networks in an encoder and decoder configuration. The best performing such models also connect the encoder and decoder through an attentionm echanisms.  We propose a novel, simple network architecture based solely onan attention mechanism, dispensing with recurrence and convolutions entirely.Experiments on two machine translation tasks show these models to be superiorin quality while being more parallelizable and requiring significantly less timeto train. Our single model with 165 million parameters, achieves 27.5 BLEU onEnglish-to-German translation, improving over the existing best ensemble result by over 1 BLEU. On English-to-French translation, we outperform the previoussingle state-of-the-art with model by 0.7 BLEU, achieving a BLEU score of 41.1.', 'description': 'Paper accepted and presented at the Neural Information Processing Systems Conference (http://nips.cc/)', 'published': '2017', 'moddate': '2018-02-12T21:22:10-08:00', 'date': '2017', 'title': 'Attention is All you Need', 'lastpage': '6008', 'start_index': 1610, 'created': '2017', 'publisher': 'Curran Associates, Inc.', 'source': '/content/attention_is_all_you_need.pdf', 'creationdate': '', 'eventtype': 'Poster', 'producer': 'PyPDF2', 'page_label': '1'}, page_content='transduction problems such as language modeling and machine translation [ 29, 2, 5]. Numerous\nefforts have since continued to push the boundaries of recurrent language models and encoder-decoder\narchitectures [31, 21, 13].\n∗Equal contribution. Listing order is random. Jakob proposed replacing RNNs with self-attention and started\nthe effort to evaluate this idea. Ashish, with Illia, designed and implemented the ﬁrst Transformer models and\nhas been crucially involved in every aspect of this work. Noam proposed scaled dot-product attention, multi-head\nattention and the parameter-free position representation and became the other person involved in nearly every\ndetail. Niki designed, implemented, tuned and evaluated countless model variants in our original codebase and\ntensor2tensor. Llion also experimented with novel model variants, was responsible for our initial codebase, and\nefﬁcient inference and visualizations. Lukasz and Aidan spent countless long days designing various parts of and'), Document(id='e833a9df-5536-4f7c-80a7-d328fdb621e2', metadata={'page': 8, 'lastpage': '6008', 'subject': 'Neural Information Processing Systems http://nips.cc/', 'moddate': '2018-02-12T21:22:10-08:00', 'page_label': '9', 'language': 'en-US', 'producer': 'PyPDF2', 'eventtype': 'Poster', 'date': '2017', 'description-abstract': 'The dominant sequence transduction models are based on complex recurrent orconvolutional neural networks in an encoder and decoder configuration. The best performing such models also connect the encoder and decoder through an attentionm echanisms.  We propose a novel, simple network architecture based solely onan attention mechanism, dispensing with recurrence and convolutions entirely.Experiments on two machine translation tasks show these models to be superiorin quality while being more parallelizable and requiring significantly less timeto train. Our single model with 165 million parameters, achieves 27.5 BLEU onEnglish-to-German translation, improving over the existing best ensemble result by over 1 BLEU. On English-to-French translation, we outperform the previoussingle state-of-the-art with model by 0.7 BLEU, achieving a BLEU score of 41.1.', 'author': 'Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin', 'start_index': 0, 'editors': 'I. Guyon and U.V. Luxburg and S. Bengio and H. Wallach and R. Fergus and S. Vishwanathan and R. Garnett', 'description': 'Paper accepted and presented at the Neural Information Processing Systems Conference (http://nips.cc/)', 'published': '2017', 'title': 'Attention is All you Need', 'total_pages': 11, 'firstpage': '5998', 'book': 'Advances in Neural Information Processing Systems 30', 'creationdate': '', 'type': 'Conference Proceedings', 'created': '2017', 'source': '/content/attention_is_all_you_need.pdf', 'creator': 'PyPDF', 'publisher': 'Curran Associates, Inc.'}, page_content='Table 3: Variations on the Transformer architecture. Unlisted values are identical to those of the base\nmodel. All metrics are on the English-to-German translation development set, newstest2013. Listed\nperplexities are per-wordpiece, according to our byte-pair encoding, and should not be compared to\nper-word perplexities.\nN d model dff h d k dv Pdrop ϵls\ntrain PPL BLEU params\nsteps (dev) (dev) ×106\nbase 6 512 2048 8 64 64 0.1 0.1 100K 4.92 25.8 65\n(A)\n1 512 512 5.29 24.9\n4 128 128 5.00 25.5\n16 32 32 4.91 25.8\n32 16 16 5.01 25.4\n(B) 16 5.16 25.1 58\n32 5.01 25.4 60\n(C)\n2 6.11 23.7 36\n4 5.19 25.3 50\n8 4.88 25.5 80\n256 32 32 5.75 24.5 28\n1024 128 128 4.66 26.0 168\n1024 5.12 25.4 53\n4096 4.75 26.2 90\n(D)\n0.0 5.77 24.6\n0.2 4.95 25.5\n0.0 4.67 25.3\n0.2 5.47 25.7\n(E) positional embedding instead of sinusoids 4.92 25.7\nbig 6 1024 4096 16 0.3 300K 4.33 26.4 213\nIn Table 3 rows (B), we observe that reducing the attention key size dk hurts model quality. This')], 'context_used': ""Source: {'author': 'Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin', 'page': 0, 'editors': 'I. Guyon and U.V. Luxburg and S. Bengio and H. Wallach and R. Fergus and S. Vishwanathan and R. Garnett', 'firstpage': '5998', 'type': 'Conference Proceedings', 'subject': 'Neural Information Processing Systems http://nips.cc/', 'language': 'en-US', 'total_pages': 11, 'book': 'Advances in Neural Information Processing Systems 30', 'creator': 'PyPDF', 'description-abstract': 'The dominant sequence transduction models are based on complex recurrent orconvolutional neural networks in an encoder and decoder configuration. The best performing such models also connect the encoder and decoder through an attentionm echanisms.  We propose a novel, simple network architecture based solely onan attention mechanism, dispensing with recurrence and convolutions entirely.Experiments on two machine translation tasks show these models to be superiorin quality while being more parallelizable and requiring significantly less timeto train. Our single model with 165 million parameters, achieves 27.5 BLEU onEnglish-to-German translation, improving over the existing best ensemble result by over 1 BLEU. On English-to-French translation, we outperform the previoussingle state-of-the-art with model by 0.7 BLEU, achieving a BLEU score of 41.1.', 'description': 'Paper accepted and presented at the Neural Information Processing Systems Conference (http://nips.cc/)', 'published': '2017', 'moddate': '2018-02-12T21:22:10-08:00', 'date': '2017', 'title': 'Attention is All you Need', 'lastpage': '6008', 'start_index': 1610, 'created': '2017', 'publisher': 'Curran Associates, Inc.', 'source': '/content/attention_is_all_you_need.pdf', 'creationdate': '', 'eventtype': 'Poster', 'producer': 'PyPDF2', 'page_label': '1'}\nContent: transduction problems such as language modeling and machine translation [ 29, 2, 5]. Numerous\nefforts have since continued to push the boundaries of recurrent language models and encoder-decoder\narchitectures [31, 21, 13].\n∗Equal contribution. Listing order is random. Jakob proposed replacing RNNs with self-attention and started\nthe effort to evaluate this idea. Ashish, with Illia, designed and implemented the ﬁrst Transformer models and\nhas been crucially involved in every aspect of this work. Noam proposed scaled dot-product attention, multi-head\nattention and the parameter-free position representation and became the other person involved in nearly every\ndetail. Niki designed, implemented, tuned and evaluated countless model variants in our original codebase and\ntensor2tensor. Llion also experimented with novel model variants, was responsible for our initial codebase, and\nefﬁcient inference and visualizations. Lukasz and Aidan spent countless long days designing various parts of and\n\nSource: {'page': 8, 'lastpage': '6008', 'subject': 'Neural Information Processing Systems http://nips.cc/', 'moddate': '2018-02-12T21:22:10-08:00', 'page_label': '9', 'language': 'en-US', 'producer': 'PyPDF2', 'eventtype': 'Poster', 'date': '2017', 'description-abstract': 'The dominant sequence transduction models are based on complex recurrent orconvolutional neural networks in an encoder and decoder configuration. The best performing such models also connect the encoder and decoder through an attentionm echanisms.  We propose a novel, simple network architecture based solely onan attention mechanism, dispensing with recurrence and convolutions entirely.Experiments on two machine translation tasks show these models to be superiorin quality while being more parallelizable and requiring significantly less timeto train. Our single model with 165 million parameters, achieves 27.5 BLEU onEnglish-to-German translation, improving over the existing best ensemble result by over 1 BLEU. On English-to-French translation, we outperform the previoussingle state-of-the-art with model by 0.7 BLEU, achieving a BLEU score of 41.1.', 'author': 'Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin', 'start_index': 0, 'editors': 'I. Guyon and U.V. Luxburg and S. Bengio and H. Wallach and R. Fergus and S. Vishwanathan and R. Garnett', 'description': 'Paper accepted and presented at the Neural Information Processing Systems Conference (http://nips.cc/)', 'published': '2017', 'title': 'Attention is All you Need', 'total_pages': 11, 'firstpage': '5998', 'book': 'Advances in Neural Information Processing Systems 30', 'creationdate': '', 'type': 'Conference Proceedings', 'created': '2017', 'source': '/content/attention_is_all_you_need.pdf', 'creator': 'PyPDF', 'publisher': 'Curran Associates, Inc.'}\nContent: Table 3: Variations on the Transformer architecture. Unlisted values are identical to those of the base\nmodel. All metrics are on the English-to-German translation development set, newstest2013. Listed\nperplexities are per-wordpiece, according to our byte-pair encoding, and should not be compared to\nper-word perplexities.\nN d model dff h d k dv Pdrop ϵls\ntrain PPL BLEU params\nsteps (dev) (dev) ×106\nbase 6 512 2048 8 64 64 0.1 0.1 100K 4.92 25.8 65\n(A)\n1 512 512 5.29 24.9\n4 128 128 5.00 25.5\n16 32 32 4.91 25.8\n32 16 16 5.01 25.4\n(B) 16 5.16 25.1 58\n32 5.01 25.4 60\n(C)\n2 6.11 23.7 36\n4 5.19 25.3 50\n8 4.88 25.5 80\n256 32 32 5.75 24.5 28\n1024 128 128 4.66 26.0 168\n1024 5.12 25.4 53\n4096 4.75 26.2 90\n(D)\n0.0 5.77 24.6\n0.2 4.95 25.5\n0.0 4.67 25.3\n0.2 5.47 25.7\n(E) positional embedding instead of sinusoids 4.92 25.7\nbig 6 1024 4096 16 0.3 300K 4.33 26.4 213\nIn Table 3 rows (B), we observe that reducing the attention key size dk hurts model quality. This\n\n""}
The provided context describes the attention mechanism introduced in the paper ""Attention is All you Need,"" but it does not contain information about recent improvements like Flash Attention.

Based on the provided text, the attention mechanism proposed in ""Attention is All you Need"" is:
*   A novel, simple network architecture based solely on an attention mechanism, completely removing recurrence and convolutions.
*   It includes scaled dot-product attention and multi-head attention.
*   Experiments on machine translation tasks showed these models to be superior in quality, more parallelizable, and required significantly less time to train compared to dominant sequence transduction models based on recurrent or convolutional neural networks.
*   For example, a single model with 165 million parameters achieved 27.5 BLEU on English-to-German translation and 41.1 BLEU on English-to-French translation, outperforming existing best ensemble and single state-of-the-art results, respectively.

Therefore, based solely on the provided text, I cannot compare the attention mechanism from the paper with Flash Attention or recommend which approach would be better for your college project, as information on Flash Attention is not available in the given context.

```
### Let's Break Down The Question

| Information Needed | Where to Find It? |
|---|---|
| Attention Mechanism Details | PDF (Vector Database) |
| Flash Attention (Different) | NOT in 2017 paper! |
| Recent Improvements | NOT in 2017 paper! |
| Project Recommendations | Needs reasoning from BOTH |

### What Our RAG DocuChat Actually Does

Question → Search Vector DB (ONE time) → Get top 2 chunks → Send to LLM → Answer 

**The Fixed Pipeline Problem:** No reasoning or external search

### What We Need

Our DocuChat is like a librarian who brings you the first book they find.

But what we need is a research assistant who:

*   Understands your question deeply
*   Plans how to find the best answer
*   Searches multiple times if needed
*   Puts everything together logically
*   Searches web if answer is not found

### The Solution: What If RAG Could Think?

This is where <b>RAG Agent</b> comes in!

*   **Analyze** the question and break it into sub-tasks
*   **Decide** which tool to use for each sub-task
*   **Execute** multiple searches across different sources
*   **Reason** through all the gathered information
*   **Synthesize** a comprehensive final answer

## What is RAG Agent?

**RAG Agent is a framework** that **enhances traditional RAG systems** by incorporating intelligent agents **to handle complex tasks** and make **decisions dynamically**.

## Traditional RAG VS Agentic RAG

**RAG (Fixed Pipeline):**

User Question → Retrieve (Always, ONE time) → Generate (Always) → Answer

**Agentic RAG (Intelligent Agent):**

User Question → Agent THINKS: ""What do I need?"" → Agent DECIDES: ""Which tool to use?"" → Agent ACTS: Executes tool(s) → Agent REASONS: Generates answer

### RAG vs Agentic RAG Comparison

| Feature | RAG | Agentic RAG |
|---|---|---|
| Retrieves context? | ✅ Yes | ✅ Yes |
| Plans next steps? | ❌ No | ✅ Yes |
| Multi-turn reasoning? | ❌ No | ✅ Yes |
| Uses tools/APIs? | ❌ No | ✅ Yes |
| Task autonomy | ❌ Only Q&A | ✅ Takes steps to complete a task |

## Let's Add Agent Capabilities to Our DocuChat RAG Application

### What We Already Have

Our existing DocuChat code has:

*   Document Loading (PyPDF Loader)
*   Text Splitting (Recursive Character-Text Splitter)
*   Vector Store (Chroma DB)
*   Embeddings (Hugging Face-Embeddings)
*   LLM (Gemini Model)

### What We Are Building

We will add the following to our existing DocuChat:

*   **Retrieval Tool** (Searches our PDF)
*   **Web Search Tool** (Searches the internet)
*   **Agent** (Decides which tool to use)

### Steps to be Followed

1.  Create RAG Agent
2.  Convert Retrieval Function to a Tool
3.  Add Web Search Tool
4.  Execute the Agent

## Step 1: Create RAG Agent

We now have two tools, but someone needs to decide which tool to use!

####The Agent can:

*   Analyze the user's question
*   Decide which tool(s) to call
*   Execute the tools
*   Generate the final answer

### Configure the Agent

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[retrieve_from_pdf, web_search_tool],
    system_prompt=system_prompt,
)
```

### Define System Prompt

```python
system_prompt = """"""You are a helpful research assistant with access to two tools:

1. retrieve_from_pdf: Use this to find information from the
   ""Attention Is All You Need"" research paper

2. TavilySearch: Use this to find current information
   not in the paper (recent events, updates, etc.)

Strategy:
- For questions about the paper content → use retrieve_from_pdf
- For questions about recent events or topics not in the paper → use TavilySearch
- DON'T make up things 
""""""
```

## Step 2: Convert Retrieval Function to a Tool

### Why Do We Need This?

Currently, our retrieval function is just a Python function:

```python
def retrieve_context(query: str, k: int = 2):

    retrieved_docs = vector_store.similarity_search(query, k=k)

    # Build context string
    docs_content = """"
    for doc in retrieved_docs:
        docs_content += f""Source: {doc.metadata}\n""
        docs_content += f""Content: {doc.page_content}\n\n""

    return docs_content, retrieved_docs
```

**Problem:** The agent cannot use this function directly.

**Solution:** Convert to Tool — the agent can understand and call it.

### Recap: Tool Syntax

```python
@tool
def function_name(parameter: str) -> str:
    """"""
    Short description of what this tool does.
    """"""
    return f""Processed: {parameter}""
```

*   `@tool`**Tool decorator** — Registers the function as a LangChain tool
*   `(parameter: str) -> str:`**Type annotations** — Define the input schema and expected output type for the LLM
*   `    """"""
    Short description of what this tool does.
    """"""` **Docstring** — Describes the tool's purpose to help the LLM decide when to use it

### Adding the Tool Decorator

```python
from langchain.tools import tool

@tool
def retrieve_from_pdf(query: str) -> str:
    """"""Retrieve information from the Attention Is All You Need research paper.""""""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    docs_content = """"
    for doc in retrieved_docs:
        docs_content += f""Source: {doc.metadata}\n""
        docs_content += f""Content: {doc.page_content}\n\n""
    return docs_content
```

We add the `@tool` decorator, return type `str`, and a descriptive docstring — together these help the agent understand what this tool does and when to use it.

## Step 3: Add Web Search Tool

### Why Do We Need Web Search?

Our retrieval tool can only search documents stored in the vector database. To answer questions about recent events not covered in our documents, we need a tool that can search the web.

### Solution: Tavily Search

To find info about latest research papers, we'll use **Tavily Search** — a search engine built specifically for AI agents (LLMs) delivering real-time, accurate, and factual results at speed.

### Install the Tavily Package

```bash
!pip install langchain-tavily
```

```python
from langchain_tavily import TavilySearch

tavily_api_key = userdata.get('TAVILY_API_KEY')

web_search_tool = TavilySearch(
    max_results=5,
    search_depth=""advanced"",
    tavily_api_key=tavily_api_key,
)
```

## Step 4: Execute the Agent

### Executing the Agent

To execute our agent, we use the invoke method which triggers the complete workflow.

All agents include a sequence of messages in their state. To invoke the agent, pass a new message with the user's query.

### Invoke the Agent

```python
user_query = """"""Compare the attention mechanism from the paper with recent improvements like Flash Attention, and tell me which approach would be better for my college project.""""""

response = agent.invoke({
    ""messages"": [{""role"": ""user"", ""content"": user_query}]
})

print(response[""messages""][-1].content)
```


###Final Code

```python
! pip install -qU  langchain langchain-huggingface sentence_transformers

from langchain_huggingface import HuggingFaceEmbeddings

# Initialize free, local embedding model
embeddings = HuggingFaceEmbeddings(
    model_name=""sentence-transformers/all-mpnet-base-v2""
)
from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name=""example_collection"",
    embedding_function=embeddings,
    persist_directory=""./chroma_langchain_db"",  # Where to save data locally, remove if not necessary
)
document_ids = vector_store.add_documents(documents=all_splits)
sample = vector_store.get(limit=1, include=[""embeddings"", ""documents""])
print(f""Embedding dimensions: {len(sample['embeddings'][0])}"")
print(sample)
print(document_ids[:3])

```
```python
!pip install -qU langchain-google-genai
!pip install langchain langchain-tavily

from langchain.chat_models import init_chat_model
from google.colab import userdata
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_tavily import TavilySearch


api_key=userdata.get('GEMINI_API_KEY')


model = init_chat_model(
    ""google_genai:gemini-2.5-flash"",
    api_key=api_key,

)


@tool
def retrieve_from_pdf(query: str) -> str:
    """"""Retrieve information from the Attention Is All You Need research paper.""""""

    retrieved_docs = vector_store.similarity_search(query, k=2)

    docs_content = """"
    for doc in retrieved_docs:
        docs_content += f""Source: {doc.metadata}\n""
        docs_content += f""Content: {doc.page_content}\n\n""

    return docs_content
    

tavily_api_key = userdata.get('TAVILY_API_KEY')
web_search_tool = TavilySearch(
    max_results=3,
    search_depth=""advanced"",
    tavily_api_key=tavily_api_key
)

system_prompt = """"""You are a helpful research assistant with access to two tools:

1. retrieve_from_pdf: Use this to find information from the
   ""Attention Is All You Need"" research paper

2. TavilySearch: Use this to find current information
   not in the paper (recent events, updates, etc.)

Strategy:
- For questions about the paper content → use retrieve_from_pdf
- For questions about recent events or topics not in the paper → use TavilySearch
""""""


agent = create_agent(
    model=model,
    tools=[retrieve_from_pdf, web_search_tool],
    system_prompt=system_prompt
)

user_query = ""Compare the attention mechanism from the paper with recent improvements like Flash Attention, and tell me which approach would be better for my college project""

response = agent.invoke({
    ""messages"": [{""role"": ""user"", ""content"": user_query}]
})

print(response[""messages""][-1].content)
```

---


# Introduction to Context Engineering

In the previous unit, we focused on RAG Agent and Adding agent capabilities to the Docuchat and we built powerful AI applications using function calling, agents, and RAG systems. Now in this unit, we will understand Context Engineering, exploring its core techniques, common failures and fixes, and how it differs from Prompt Engineering.


### Challenges

As we built more complex applications, you might have noticed a pattern:


*   **Agents** sometimes **forget important information** mid-conversation
*   **Performance degrades** as conversations get longer
*   Relevant **information gets** ""**lost**"" in long context windows
*   **Costs increase** with larger prompts

### Traditional Approach vs Reality

**Traditional Approach:** Focus on crafting the perfect prompt with the right words and instructions.

**Reality:** Modern AI applications need more than good prompts — they need intelligent information management.

##Evolution of Prompt Engineering (Context Engineering)

### Introduction To Context Engineering

Context engineering is the art and science of filling the LLM's context window with just the right information, in the right format, at the right time to accomplish a task.

### Why It Matters

While the term ""Context Engineering"" is new, the idea isn't. Context engineering helps us solve a key challenge in AI: managing what information flows into and out of AI systems.

### Analogy

Just like a computer needs the right data loaded in RAM to run programs well, your AI needs the right context to perform tasks effectively.

*   CPU → LLM
*   RAM (Limited) → Context Window (Limited)
*   OS -> Context Engineering

### The Shift In Approach

Instead of writing perfect prompts, we build systems that automatically gather and organize information for the model. The system arranges everything so the AI can use it effectively:

*   Past conversations
*   User details
*   Data Sources (RAG)
*   Available tools

### Components of Context Engineering

*   System Instructions
*   Conversation History/Memory
*   Retrieved Knowledge
*   Tool Descriptions
*   Current State
*   User Prompt

<MultiLineNote>
Context Engineering brings together RAG, State/History, Memory, Structured Outputs, and Prompt Engineering.
</MultiLineNote>
### Set Up Context: Claude Projects/Custom GPT
<a href=""https://claude.ai"" target=""_blank"">Claude</a>
*   Upload your semester timetable and exam schedule
*   Add your current course materials and lecture notes
*   Include previous assignment grades and feedback
*   Upload syllabus and weightage details for each course

### Enhanced System Instructions

**System Instructions:**

```
You are an academic study assistant for engineering students. You have access to: - Student's current semester subjects and exam schedule - Current course materials - Grades and assignment feedback - Syllabus with weightage
```

**Files**
<a href=""https://nkb-backend-ccbp-media-static.s3-ap-south-1.amazonaws.com/ccbp_prod/media/content_loading/uploads/cc1bad21-242a-48fa-942f-3d29c9460361_Academic%20Files.zip"" target=""_blank"">Academic Files</a>

<br>

**Student question:** 

```
What should I focus on for my upcoming mid-semester exams?
```

The system provides an enhanced response based on all the uploaded context.

## Context vs Prompt Engineering

| | Prompt Engineering | Context Engineering |
|---|---|---|
| Focus | Focuses on how you ask the question | Focuses on everything the model sees before responding |
| Scope | The words, tone, and formatting of your input | Includes prompts, system instructions, retrieved documents, memory, tools, and state |
| Example | ""Summarize this in 3 bullet points"" | Required for complex, multi-step applications and AI agents |

### When to Use Context Engineering

*   Building AI agents or applications
*   Tasks requiring memory across conversations
*   Systems that need to access external tools or databases
*   Complex, multi-step workflows
*   Production applications

### When to Use Prompt Engineering

*   Simple chatbot conversations
*   One-shot Q&A tasks
*   Text summarization or translation
*   Quick factual queries

---

## Common Context Failures and Fixes

### Failure 1: Context Poisoning

**What happens:** The AI saves incorrect information and keeps using it in future responses.

**Example:** One piece of bad data spreads and affects all future decisions.

**Fixes:**

*   Check if information is accurate before saving
*   Only allow trusted sources to write to memory
*   Keep questionable information separate until confirmed

### Failure 2: Context Distraction

**What happens:** Too much information makes the model lose focus on what matters.

**Fixes:**

*   Summarize old conversations instead of keeping everything
*   Pull only the relevant parts, not entire documents
*   Delete outdated or completed information
*   Keep only what's needed for the current task

### Failure 3: Context Confusion

**What happens:** The AI gets confused when it receives too many tools or unclear instructions about what to do.

**Fixes:**

*   Write clear, specific tool descriptions (not vague ones)
*   Show examples of when to use each tool
*   Set clear rules for which tool handles what
*   Use structured formats so the model knows what to expect

### Failure 4: Context Clash

**What happens:** Contradictory information from different sources creates inconsistent behavior.

**Fixes:**

*   Set priority order (which source to trust)
*   Add rules for handling conflicts automatically
*   Remove old information that contradicts new facts
*   Keep one single source of truth for each type of data

---

## Core Context Engineering Techniques

### Technique 1: Writing Context

Saving information outside the context window for later use.

**The Problem and Solution**

<b>Problem:</b>Complex multi-step tasks overload the context window with too much information.

<b>Solution:</b>Use a ""scratchpad"" — external storage where the AI saves notes, plans, and intermediate results outside the main context window.

** Implementation Methods**

*   File writes (simple text files or JSON)
*   Database inserts (vector databases, SQL databases)
*   Structured memory (LangGraph state, message queues)
*   Long-term memory systems (LangGraph state)

** Benefits**

1.  <b>Prevents overload</b> — Stays within token limits
2.  <b>Remembers across sessions</b> — Information persists between conversations
3.  <b>Keeps AI focused</b> — Main context stays clean and relevant

** Example: Claude Code's Scratchpad**

When working on a large codebase, Claude Code uses a ""think"" tool as a scratchpad:

```json
{
  ""name"": ""think"",
  ""thought"": ""User wants to refactor the login module. Let me consider the current structure, identify pain points, and plan the approach before making changes...""
}
```

Notes are saved outside the main conversation, preventing it from being lost as the context fills up with code.

<MultiLineWarning text=""Research Result"">

Anthropic found the ""think"" tool improved performance by 54% on complex customer service tasks.

</MultiLineWarning>

### Technique 2: Selecting Context

Retrieving exactly the right information when needed. Rather than giving the model everything, pull in information dynamically based on the current task.

**Methods**

<b>Retrieval Augmented Generation (RAG):</b>

*   Use semantic search to find relevant documents
*   Hybrid search combining keyword + semantic matching
*   Return only relevant sections, not entire documents

<b>Tool-Based Selection:</b>

*   Model calls specific tools to fetch needed data
*   Tools return structured, filtered information
*   Example: Instead of loading entire database, query for specific records

<b>Contextual Retrieval:</b>

*   Fetch information based on current state/task
*   Use conversation context to refine what's retrieved
*   Prioritize recent and relevant info over comprehensive

### Technique 3: Compressing Context

Reducing context size while preserving important information. Reliable on longer tasks, but hard to get right.

**The Problem and Solution**

<b>Problem:</b>

*   Beyond large number of tokens, models start repeating old actions instead of thinking fresh
*   They may ""forget"" instructions from the beginning
*   Costs increase dramatically

<b>Solution:</b>Periodically summarize older content, keeping recent messages intact.

- Summarization
- Filtering
- Abstraction


### Technique 4: Isolating Context

Splitting work across specialized agents with focused context. Instead of one agent juggling everything, distribute work, if possible.

**Methods**

- Multi-Agent Decomposition
- Focused Context Per Agent
- Context Passing

---

## The Quality Over Quantity Principle

<b>More context ≠ Better performance.</b><br>


**Context rot:** As input context grows, LLM performance drops in unpredictable ways.

*   Longer context = higher cost AND often lower quality
*   Performance drop depends on model and task — there is no single safe limit for number of tokens
*   A focused 300-token context can outperform an unfocused 100,000+ token context

<a href=""https://research.trychroma.com/context-rot"" target=""_blank"">https://research.trychroma.com/context-rot</a>

## The Key Insight

> ""Context engineering is effectively the #1 job of engineers building AI agents""
> — Cognition (Devin AI)

---

# Integrating MCP

In our previous sessions, we learned about Context Engineering, Context Engineering vs Prompt Engineering, four core techniques of Context Engineering, and common failures and fixes.

We built the SkillMap Agent using LangChain with Google Gemini, Tavily, and JSearch to deliver market insights and live job links, and also developed the DocuChat RAG application with a complete document-to-vector pipeline along with an AI-Powered Conversational Interview Assistant.

Now in this unit, we will learn how to integrate external tools using MCP in LangChain agents, configure MCP clients, and retrieve tools from MCP servers.

# Integrate external tools using MCP
## Model Context Protocol

MCP is a protocol for providing the context to the models.

*   **Model** — LLMs / AI Agents
*   **Context** — Information on how and when to use the tools
*   **Protocol** — Set of rules to follow for communication

MCP standardizes how AI applications interact with external systems:

*   Prompts
*   Tools
*   Resources

### Core Components

*   **MCP Host** — The application that contains the LLM
*   **MCP Client** — Maintains a dedicated connection to one MCP server to access the tools, resources or prompts
*   **MCP Server** — External systems that provide tools/capabilities that our agent can use (like Google Drive, Slack, LinkedIn)

###How to Integrate External Tools Using MCP in SkillMap Agent

**Initial Code**
<a href=""https://colab.research.google.com/drive/1YscNUyhOFvp7MVuExmZ5I8aqv_8BwKMO#scrollTo=FjVX3AO0Tqdi"" target=""_blank"">SkillMap Agent Colab</a>

## Integrating MCP in SkillMap Agent

### LangChain MCP Adapters

LangChain provides a package called `langchain-mcp-adapters` which allows agents to use tools defined on MCP servers.

```bash
!pip install langchain-mcp-adapters
```

### Configuring the MCP Client

`langchain-mcp-adapters` provides `MultiServerMCPClient` to manage connections to MCP servers simultaneously.

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
```

We need to initialize the `MultiServerMCPClient` with a dictionary defining the connection details for our MCP servers.

#### MultiServerMCPClient - Syntax

```python
client = MultiServerMCPClient(
    {
        ""weather"": {
            ""transport"": ""How to communicate with the server"",
            ""url"": ""Where the MCP server is running"",
            ""headers"": {
                ""HTTP headers sent with each request"",
            },
        }
    }
)
```

*  `client = MultiServerMCPClient` Creates a client object that can connect to multiple MCP servers
*   `""weather""` — A custom name you choose to identify this server

### Ways to Integrate MCP Servers

MCP supports two primary ways to communicate with an MCP server:

1.  **Streamable HTTP** — Uses HTTP POST requests for client-to-server communication
2.  **STDIO** — Uses standard input/output streams and recommended for local deployments

### Integrating MCP in SkillMap Agent

Let's start by setting up our MCP client for the SkillMap Agent:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient(
    {
        ""mcp_tavily"": {
            ""transport"": ""http"",
            ""url"": ""????"",
        }
    }
)
```

## MCP Servers List

MCP servers are available from multiple sources:

* <a href=""https://platform.composio.dev/"" target=""_blank"">Composio</a>
* <a href=""https://smithery.ai"" target=""_blank"">Smithery</a>
* <a href=""https://pipedream.com/"" target=""_blank"">Pipedream</a>
* <a href=""https://github.com/modelcontextprotocol/servers"" target=""_blank"">MCP (Model Context Protocol Servers)</a>
* <a href=""https://mcp.so/"" target=""_blank"">MCP.so</a>

### Using Composio for MCP Servers

- **Composio** is a platform that provides MCP servers to connect tools to our agent.

## Configuring MCP Server

### Steps

1.  Get Composio MCP server URL for Tavily Search
2.  Configure and connect to the MCP server using the MCP Client

### Creating MCP Servers

- Go to MCP <a href=""https://platform.composio.dev/"" target=""_blank"">Composio</a> dashboard and login
2.  Go to MCP Configs and Create Config
- Select Dedicated Server and Create Server for Tavily with All Tools 
- Connect account with Tavily API key
- Copy the HTTP endpoint 


### Integrating MCP in SkillMap Agent with Composio URL

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient(
    {
        ""mcp_tavily"": {
            ""transport"": ""http"",
            ""url"": ""https://backend.composio.dev/v3/mcp/a339a263-23f2-470b-9bea-e5ce36dc9531/mcp?user_id=pg-test-763f4e60-308c-417a-821c-c66b46b29d7e"",
        }
    }
)
```

## Retrieving Tools from MCP

`MultiServerMCPClient` class provides methods that allows us to access:

*   Tools
*   Prompts
*   Other resources

Now that we have configured our MCP client, let's retrieve the tools available from the server.

`client.get_tools()` is an async method used to retrieve tools from MCP servers:

```python
tools = await client.get_tools()
```

### Why get_tools() is Async

The `client.get_tools()` method is asynchronous because:

*   **Network Communication** — Makes HTTP requests to fetch tools from the MCP server
*   **Non-blocking** — `await` lets other tasks run while waiting for the response

### Retrieving Tools

```python
async def skill_map_agent():
    mcp_tools = await client.get_tools()

  
```

### Combining MCP and LangChain Custom Tools

```python
async def skill_map_agent():
    mcp_tools = await client.get_tools()

    # Combine MCP tools with our custom tools
    all_tools = mcp_tools + [search_jobs]
```

### Providing Tools to Agent

```python
async def skill_map_agent():
    mcp_tools = await client.get_tools()

    # Combine MCP tools with our custom tools
    all_tools = mcp_tools + [search_jobs]

    agent = create_agent(
        model=model,
        tools=all_tools,
        system_prompt=system_prompt,
        debug=True
    )
```

### Updating System Prompt

```python
system_prompt = """"""You are a Skill-to-Career Mapping assistant that helps students understand skill demand and find matching job opportunities.

You have access to these tools:
- search tool: Search for industry demand, salary insights, and career trends
- search_jobs: Find actual job listings requiring specific skills

Help the student by researching the skill they ask about and finding relevant opportunities.

Present results in a clean, readable format with clear sections and proper spacing. Include all job details with apply links. Don't use markdown format.""""""
""""""
```

### MCP Tools → LangChain Tools

LangChain converts MCP tools into LangChain tools, making them directly usable in any LangChain agent.

### Executing the Agent

- When using MCP tools, the agent may need to make network calls to the MCP server during execution.

- `ainvoke()` is the asynchronous version of `invoke()` that properly handles these network operations.

### Executing the Agent using ainvoke()

```python
from langchain.agents import create_agent

async def skill_map_agent():

  mcp_tools = await client.get_tools()

  # Combine MCP tools with our custom tools
  all_tools = mcp_tools+ [search_jobs]

  agent = create_agent(
    model=model,
  tools=all_tools,
  system_prompt=system_prompt,
  debug=True

  )
  user_query = ""What's the demand for generative ai in the industry ""

  response = await agent.ainvoke({
    ""messages"": [{""role"": ""user"", ""content"": user_query}]
  })
  print(response[""messages""][-1].content[0][""text""])

```

### Running the Async Function

```python
from langchain.agents import create_agent

async def skill_map_agent():

  mcp_tools = await client.get_tools()

  # Combine MCP tools with our custom tools
  all_tools = mcp_tools+ [search_jobs]

  agent = create_agent(
    model=model,
  tools=all_tools,
  system_prompt=system_prompt,
  debug=True

  )
  user_query = ""What's the demand for generative ai in the industry ""

  response = await agent.ainvoke({
    ""messages"": [{""role"": ""user"", ""content"": user_query}]
  })
  print(response[""messages""][-1].content[0][""text""])


await skill_map_agent()
```
`await skill_map_agent()`
*   This executes our async function and waits for it to complete
*   Google Colab supports top-level `await` (you can use `await` directly in notebook cells)
*   The agent will process the query, use the appropriate tools, and return the answer

## Using MCP Server Provided by Tavily Directly

- <a href=""https://app.tavily.com/home"" target=""_blank"">Tavily</a> is also providing a remote MCP server we can use directly in our application.



### Integrating Tavily MCP Server

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient(
    {
        ""mcp_tavily"": {
            ""transport"": ""http"",
            ""url"": ""https://backend.composio.dev/v3/mcp/a339a263-23f2-470b-9bea-e5ce36dc9531/mcp?user_id=pg-test-763f4e60-308c-417a-821c-c66b46b29d7e"",
        }
    }
)

```

## MCP: Advantages

*   **Plug & Play** — As the MCP ecosystem is rapidly growing, we can now directly integrate any MCP server without any additional work
*   **Flexibility and Scalability** — Can easily switch between different tools without rewriting integrations
*   **Context Rich** — Provides correct usage of tools with the clear context of the tools

Once we understand how to work with MCP, we can connect to any MCP-compatible resource using the same patterns and techniques.

### Final Code

```python
!pip install -U langchain-google-genai
!pip install langchain langchain-tavily
!pip install langchain-mcp-adapters

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.chat_models import init_chat_model
from google.colab import userdata

google_api_key = userdata.get('GEMINI_API_KEY')
model = init_chat_model(""google_genai:gemini-2.5-flash"", api_key=google_api_key)

from langchain_tavily import TavilySearch
from google.colab import userdata


tavily_api_key = userdata.get('TAVILY_API_KEY')
skill_demand_tool = TavilySearch(
    max_results=5,
    search_depth=""advanced"",
    tavily_api_key=tavily_api_key,
)

import requests
from langchain.tools import tool
from google.colab import userdata

@tool
def search_jobs(skill: str, location: str) -> list:
  """"""Search for jobs requiring a specific skill using JSearch API from RapidAPI.""""""
  print(f""\nCalling search_jobs tool"")
  print(f""Searching jobs for: {skill} in {location}"")

  rapidapi_key = userdata.get('RAPIDAPI_KEY')

  url = ""https://jsearch.p.rapidapi.com/search""
  headers = {
    ""x-rapidapi-key"": rapidapi_key,
    ""x-rapidapi-host"": ""jsearch.p.rapidapi.com""
  }
  querystring = {
    ""query"": f""{skill} in {location}"",
    ""page"": ""1"",
    ""country"": ""in"",
    ""employment_types"": ""INTERN,FULLTIME"",
    ""job_requirements"": ""no_experience,under_3_years_experience""
  }
  response = requests.get(url, headers=headers, params=querystring)
  data = response.json()
  jobs = data.get(""data"", [])
  print(f""Found {len(jobs)} jobs\n"")

  result = []
  for job in jobs:
    result.append({
      ""title"": job.get(""job_title""),
      ""company"": job.get(""employer_name""),
      ""location"": job.get(""job_city""),
      ""apply_link"": job.get(""job_apply_link"")
    })
  return result

system_prompt = """"""You are a Skill-to-Career Mapping assistant that helps students understand skill demand and find matching job opportunities.

You have access to these tools:
- search tool: Search for industry demand, salary insights, and career trends
- search_jobs: Find actual job listings requiring specific skills

Help the student by researching the skill they ask about and finding relevant opportunities.

Present results in a clean, readable format with clear sections and proper spacing. Include all job details with apply links. Don't use markdown format.""""""



client = MultiServerMCPClient(
    {
        ""mcp_tavily"": {
            ""transport"": ""http"",
            ""url"": ""https://backend.composio.dev/v3/mcp/a339a263-23f2-470b-9bea-e5ce36dc9531/mcp?user_id=pg-test-763f4e60-308c-417a-821c-c66b46b29d7e"",
        }
    }
)

from langchain.agents import create_agent

async def skill_map_agent():

  mcp_tools = await client.get_tools()

  # Combine MCP tools with our custom tools
  all_tools = mcp_tools+ [search_jobs]

  agent = create_agent(
    model=model,
  tools=all_tools,
  system_prompt=system_prompt,
  debug=True

  )
  user_query = ""What's the demand for generative ai in the industry ""

  response = await agent.ainvoke({
    ""messages"": [{""role"": ""user"", ""content"": user_query}]
  })
  print(response[""messages""][-1].content[0][""text""])


await skill_map_agent()
```

---

# Building Multi Agent Systems Using Crew AI

In our previous session, we learned about integrating MCP Servers in LangChain Agents — integrating MCP in LangChain, using MultiServerMCPClient, Tavily MCP Server, and retrieving tools from MCP using `get_tools()`.
Now in this unit, we will understand Multi-Agent Systems, and learn how to build multi-agent systems using CrewAI and the core components of Crew AI.

## AI Agent

An AI agent is a system that can operate independently to achieve a specific goal without constant human intervention.

## Beyond Single Agents

Many challenges can be solved with a ""Single agent, multi-tool"" approach, where one agent is given access to a variety of tools and knowledge sources.

### Example

User asks: ""Research latest iPhone and create a comparison doc""

**Single Agent Process:**

1.  Search the web for iPhone info
2.  Read multiple articles
3.  Organize information
4.  Create document
5.  Format it nicely

(All done by ONE agent)

### Challenges of Single-Agent Systems

As tasks become more complex, a single agent might face significant challenges:

*   **Tool Overload** — Managing too many tools can make the Agent harder to make clear decisions. 
*   **Contextual Limitations** — LLMs struggle with performance when context grows.
*   **Specialization Deficiency** — A single agent cannot master diverse tasks.


# Introduction to Multi-Agent Systems

### What is a Multi-Agent System?

A Multi-Agent System is a team of AI agents with specialized roles working together to solve complex tasks efficiently.

### Team of AI Specialists

Multi-Agent Systems are like having a team of AI specialists, where:

*   Each agent has <b>a specific role and expertise</b>
*   Agents can <b>communicate</b> with each other
*   They <b>collaborate</b> to solve complex problems
*   They can <b>share information</b> and <b>delegate tasks</b>
*   Finally, they produce a single output

### Example - Making a Movie

*    **Director** — Plans the overall vision
*    **Actors** — Perform the scenes
*    **Cinematographer** — Handles camera work
*    **Music Composer** — Creates background score
*    **Editor** — Puts everything together

Each person is an expert in their role, and they work together to create the final movie!


### Example - Planning a Wedding

Imagine you're planning a wedding. You need:

*   Someone to handle <b>decorations</b> and make everything beautiful
*   Another person to manage the <b>food</b> and catering
*   Someone to <b>coordinate with guests</b> and handle RSVPs
*   Another to handle <b>entertainment</b> and music

Each person has their own expertise and responsibilities, but they all work together toward the same goal: creating an amazing celebration. This is exactly how Multi-Agent AI Systems work!

### How It Works

Just like each person in a team has a unique role but everyone works toward one goal, a Multi-Agent AI system also works in a similar manner. 

Have you worked in a team where different strengths of different people made the result better than one person doing everything?

### Real World Applications - Trading Systems

Trading systems use multiple agents to monitor markets, analyze trends, execute trades, and manage risk, enabling faster and smarter trading than single-agent systems.

*   **Monitoring Agent** — Collects real-time and historical market data
*   **Strategy Agent** — Analyzes and decides trading actions
*   **Execution Agent** — Places trades efficiently
*   **Risk Management Agent** — Ensures safe and controlled trading

### Real World Applications - Vehicle Systems

Autonomous vehicles use specialized agents for perception, planning, traffic, and safety, working together to navigate complex situations safely.

*   **Perception & Control Agent** — Senses & understands the vehicle's environment and controls the vehicle
*   **Planning Agent** — Plans the vehicle's route
*   **Safety Agent** — Monitors the system for safety (speed limit, etc.)

### Key Characteristics of Multi-Agent Systems

*   **Collaboration** — Agents interact and share information to tackle complex challenges
*   **Autonomy** — Each agent operates independently, making its own decisions
*   **Specialization** — Agents are designed for specific tasks, enhancing efficiency
*   **Scalability** — New agents can be added to the system easily as needs grow

# Building Multi Agent Systems

## Frameworks

There are multiple frameworks that allow us to build multi-agent systems:


*   **<a href=""https://www.crewai.com"" target=""_blank"">CrewAI</a>** — Team-based AI agents working together
*   **<a href=""https://microsoft.github.io/autogen"" target=""_blank"">AutoGen</a>** — AI agents that talk to each other
*   **<a href=""https://github.com/openai/swarm"" target=""_blank"">OpenAI Swarm</a>** — Graph-based multi-step agent workflows
*   **<a href=""https://www.langchain.com"" target=""_blank"">LangChain</a>** — Building LLM-powered applications

## Using CrewAI

**CrewAI** is an <b>open-source Python framework</b> that allows us to build, <b>production-ready</b> and collaborative <b>AI agent teams</b> to tackle complex tasks.


## Core Components of CrewAI

CrewAI has three core components:

1.  **Agents**
2.  **Tasks**
3.  **Crew**

### 1. Agents

In CrewAI, an agent is an AI specialist with:

*   **A role** (what they do)
*   **A goal** (what they aim to achieve)
*   **A backstory** (their expertise and personality)
*   **Tools** (capabilities they can use)

Each AI Agent in the Crew has a specific role capable of carrying out multiple role-related Tasks. Agents are equipped with Tools that facilitate them completing the jobs.

** Example - Research Agent**

*   <b>Role:</b> Senior Research Analyst
*   <b>Goal:</b> Find accurate, up-to-date information
*   <b>Backstory:</b> Expert researcher skilled at gathering insights
*   <b>Tools:</b> Web search

**Example - Content Writer Agent**

*   <b>Role:</b> Creative content writer
*   <b>Goal:</b> Write engaging blog posts
*   <b>Backstory:</b> Expert writer with 10 years of experience
*   <b>Tools:</b> Web search, document creation



** Agents are workers in Multi Agent System**


Think of agents as the workers in the system:

*   Each agent is autonomous and specializes in one task
*   Works independently but shares information with other agents
*   Sometimes, relies on others' outputs to do their job better
*   Can also delegate tasks to other agents as and when required

### 2. Tasks

Tasks are specific jobs we want our agents to complete. Each task should have:

*   Clear description of what needs to be done
*   Which agent should handle it
*   Expected output format

#### Example

| | Task 1 | Task 2 |
|---|---|---|
| <b>Task</b> | Research latest AI trends | Use the research report to craft a compelling blog |
| <b>Assigned to</b> | Research Agent | Content Writer Agent |
| <b>Expected Output</b> | Summary report with 5 key trends | A well-written blog post |

### 3. Crew

The crew is your complete team — all agents working together with a defined process:

*   <b>Sequential</b> — Agents work one after another
*   <b>Hierarchical</b>  — One agent manages others
*   <b>Parallel</b> — Agents work simultaneously

**CrewAI Allows Us To…**

*   Create multiple AI agents with different roles
*   Define how they work together
*   Assign them specific tasks
*   Coordinate their collaboration automatically

** Installing CrewAI**

```bash
!pip install -U crewai
```

**Multi Model**

While building multi-agent systems, think of yourself as a manager/leader:

*   What is the Goal?
*   What kind of people would I need to hire to get this done?
*   What is the Process?

---

# Building a Game Development Crew

In our previous session, we learned about Multi-Agent Systems, their key characteristics, and CrewAI's core components — Agents, Tasks, and Crew.

Now in this unit, we will build a Game Development Crew using CrewAI — creating specialized AI agents, defining tasks, assembling the crew, and executing it to turn a game idea into a playable prototype.

>**Quick Question**
> Have you ever played a video game and thought, ""I want to make my own game!""?


##Building a Game Development Crew

Imagine You have a brilliant game idea. You can see the characters, you know how you want your game to be. But turning that vision into a playable prototype requires a team, specialized skills, and a lot of time.

<b>Brilliant Game Idea → Assemble Team → Develop Prototype → Deploy Prototype</b>

###High-Performance Game
For a Simple Game, You Typically Need

*   **Game Designer** — Creates game concepts and designs from the given idea
*   **Software Engineer** — Figures out logic and writes actual game code
*   **QA Engineer** — Tests and finds bugs

Instead of hiring 3 people, you can create 3 AI agents, each specialized in one role. They communicate, collaborate, and complete tasks just like a real team!

### What to Achieve?

**Our Goal:** Create a crew/team of AI agents that can design and plan a simple 2D platformer/jumper game.

**Our Team Structure:**

*   **Game Designer Agent** — Creative mind
*   **Software Engineer Agent** — Technical brain
*   **QA Engineer Agent** — Quality checker

### Initial Code

- <a href=""https://colab.research.google.com/drive/1WQjLfKNpDZf6bVmQEnMnLXhb6bwNvjZ0#scrollTo=EpyaeIDlIr99"" target=""_blank"">Building a Game Development Crew initial code</a>

##Steps to Build Game Development Crew

1.  Creating Agents
2.  Defining Tasks
3.  Assembling the Crew
4.  Executing the Crew

## Step 1: Creating Agents

### Creating Agents in CrewAI

There are two ways to create agents in CrewAI:

*   Using YAML Configuration File
*   Defining directly in code

Let's see how we can define agents in Python.

### Creating Agents - Syntax

```
sample_agent = Agent(
    role=""Title of the agent"",
    goal=""The objective the agent must achieve"",
    backstory=""Context that shapes behavior, tone, and decisions"",
    tools=[],
    llm=Model to be used (Current default is OpenAI's GPT-4),
    verbose=True/False (Shows agent's reasoning and steps)
)
```
###Creating Agent for Game Designer

```python
game_designer = Agent(
    role=""Creative Game Designer"",
    goal=""Come up with fun, feasible game concepts and detailed mechanics based on user idea"",
    backstory=
      ""You are an experienced game designer.""
      ""You excel at turning vague ideas into clear, exciting game designs including:""
      ""- core loop, rules, win/lose conditions""
      ""- basic entities (player, enemies, items)""
      ""- controls and feel""
      ""Keep it simple enough to implement in pure Python + Pygame in one file."",
    verbose=True,
    llm=llm,
)
```

- Since no tools are required for designing a game, we haven’t provided any tools
- The model to be used currently defaults to GPT-4

Let’s see how we can integrate Gemini LLM

### Integrating Different LLMs

**<a href=""https://www.crewai.com"" target=""_blank"">CrewAI </a>**allows us to integrate with multiple LLM providers:

* **<a href=""https://openai.com/"" target=""_blank"">GPT (OpenAI)</a>**
* **<a href=""https://gemini.google.com/app"" target=""_blank"">Gemini (Google)</a>**
* **<a href=""https://www.llama.com/models/llama-3/"" target=""_blank"">LLaMA 3 (Meta)</a>**
* **<a href=""https://claude.ai/"" target=""_blank"">Claude (Anthropic)</a>**


### Integrating Google Gemini Models

CrewAI provides integration with Google Gemini through the Python package named Google GenAI.

```bash
!pip install ""crewai[google-genai]""
```

### Defining LLM

CrewAI provides an `LLM` class that allows us to integrate different models.

```python
from crewai import Agent, LLM

llm = LLM(
    model=""gemini/gemini-2.5-flash"",
)
```

### Storing API Keys

Store the Gemini API key in Colab Secrets:

```python
from crewai import Agent, LLM
from google.colab import userdata

gemini_api_key = userdata.get('GEMINI_API_KEY')

llm = LLM(
    model=""gemini/gemini-2.5-flash"",
    api_key=gemini_api_key
)
```

### Providing LLM to Agent

```python
from crewai import Agent,LLM
from google.colab import userdata

gemini_api_key = userdata.get('GEMINI_API_KEY')


llm = LLM(
   model=""gemini/gemini-2.5-flash"",
   api_key=gemini_api_key
)

game_designer = Agent(
    role=""Creative Game Designer"",
    goal=""Come up with fun, feasible game concepts and detailed mechanics based on user idea"",
    backstory=
      ""You are an experienced game designer.""
      ""You excel at turning vague ideas into clear, exciting game designs including:""
      ""- core loop, rules, win/lose conditions""
      ""- basic entities (player, enemies, items)""
      ""- controls and feel""
      ""Keep it simple enough to implement in pure Python + Pygame in one file."",
    verbose=True,
    llm=llm,
)
```

### Creating Agent for Software Engineer
```python
senior_engineer = Agent(
   role=""Senior Python Game Developer"",
   goal=""Write clean, working Python code (using Pygame) for the described game"",
    backstory=
        ""You are a senior software engineer specialized in Python game development with Pygame.""
        ""You write structured, readable code with:""
        ""- Proper game loop, event handling, drawing""
        ""- Comments explaining key parts""
        ""- Error handling where needed""
        ""You always produce a complete, runnable .py file."",
   verbose=True,
   llm=llm,
)
```



Developers excel at problem-solving, not memorization. When stuck, they refer to official documentation. So let's provide a search tool to our software engineer agent.

### CrewAI Tools

Similar to LangChain, CrewAI also provides a suite of built-in tools which we can provide to Agents to enhance their capabilities.

CrewAI supports tools from:

*   CrewAI Toolkit
*   LangChain Tools

### Installing CrewAI Tools

```bash
!pip install 'crewai[tools]'
```

Some available tools:

* <a href=""https://serper.dev/"" target=""_blank"">SerperDev Tool</a> — Allows the agent to fetch up-to-date information from the internet  
* <a href=""https://docs.crewai.com/en/tools/ai-ml/dalletool"" target=""_blank"">DALL·E Tool</a> — Creates images based on text descriptions  
* <a href=""https://docs.crewai.com/en/tools/file-document/filereadtool"" target=""_blank"">File Search / FileRead Tool</a> — Retrieves information from uploaded files or external knowledge sources  

### Integrating SerperDev Tool

SerperDev tool allows AI agents to perform real-time Google search and access current information from the web.

```python
from crewai_tools import SerperDevTool

search_tool = SerperDevTool()
```

Store the Serper API key in Colab Secrets. Get the API key from - <a href=""https://serper.dev/"" target=""_blank"">Serper.dev</a>

### Providing Tools to the Software Engineer Agent

```python
from crewai_tools import SerperDevTool

serper_api_key = userdata.get('SERPER_API_KEY')

search_tool = SerperDevTool(api_key=serper_api_key)


senior_engineer = Agent(
   role=""Senior Python Game Developer"",
   goal=""Write clean, working Python code (using Pygame) for the described game"",
    backstory=
        ""You are a senior software engineer specialized in Python game development with Pygame.""
        ""You write structured, readable code with:""
        ""- Proper game loop, event handling, drawing""
        ""- Comments explaining key parts""
        ""- Error handling where needed""
        ""You always produce a complete, runnable .py file."",
   verbose=True,
   llm=llm,
)
```


### Creating QA Agent

```python
qa_engineer = Agent(
    role=""QA Engineer & Code Reviewer"",
    goal=""Test, review, and improve the code for bugs, playability, and completeness"",
    backstory=
        ""You are a meticulous QA engineer and code reviewer.""
        ""You carefully check:""
        ""- Does the code run without errors?""
        ""- Does it implement ALL the designed features?""
        ""- Is it fun/playable? Any obvious balance issues?""
        ""- Code style, variable names, comments""
        ""Suggest fixes or small improvements and output the FINAL improved code."",
    verbose=True,
    llm=llm,
)

```

## Step 2: Defining Tasks

In the CrewAI framework, a Task is a specific assignment completed by an Agent. Each task should have:

*   **Description** — What needs to be done
*   **Agent** — Who will do this task
*   **Expected Output** — What the final result should look like

### Creating Tasks in CrewAI

There are two ways to define tasks:

*   Defining through YAML file
*   Defining directly in code

### Creating Tasks - Syntax

```python
research_task = Task(
    description="""",
    expected_output="""",
    agent=researcher
)
```

### Creating Task for Game Designer

```python
from crewai import Task

task_design = Task(
    description=
        ""Take the user's game idea: {game_idea}""
        ""1. Clarify and expand it into a fun, simple 2D game""
        ""2. Describe: objective, controls, entities, win/lose""
        ""3. Keep scope small (one level, basic mechanics)""
        ""Output format:""
        ""## Game Design Document""
        ""- Title: ...""
        ""- Genre: ...""
        ""- Objective: ...""
        ""- Controls: ...""
        ""- Entities: ...""
        ""- Mechanics: ..."",
    expected_output=""A clear markdown Game Design Document"",
    agent=game_designer
)
```

**Note:** Description here is not a formatted string. `{game_idea}` will be given later and managed by CrewAI.

### Creating Task for Software Engineer

How does the Engineer know what the Designer has created?

```python
task_code = Task(
    description=
        ""Using the game design from the previous task""
        ""Write a COMPLETE, standalone Python script using Pygame that implements the game.""
        ""- Include import pygame, sys, random (if needed)""
        ""- Full game loop, init, events, update, draw""
        ""- Make it runnable with python game.py""
        ""- Add simple comments""
        ""- The main game loop must be exposed in the python code, it should not be inside any function like main""
        ""- Final answer MUST be ONLY the Python code and Instructions on how to play the game"",
    expected_output=""A complete runnable Pygame Python script"",
    agent=senior_engineer,
    context=[task_design]
)
```

### The Context Parameter

Tasks accept a parameter called `context` which allows us to pass the output from previous tasks as input to the current one. It's how the team shares information and builds on each other's work.

### Creating Task for QA Engineer

For final review, the QA engineer receives both the design document and the code via the context list.

```python
task_review = Task(
    description=
        ""Review the Python code from the previous task.""
        ""1. Check for syntax/runtime errors""
        ""2. Verify it matches the design document""
        ""3. Test mentally: does it have init, loop, quit handling, drawing?""
        ""4. Suggest fixes/improvements if needed""
        ""5. Output the FINAL, improved, ready-to-run code""
        ""Your final answer MUST be ONLY the complete Python code along with the instructions on how to play the game"",
    expected_output=""Final polished, runnable Pygame Python script and instructions on how to play the game"",
    agent=qa_engineer,
    context=[task_design, task_code]
)
```

## Step 3: Assembling the Crew

- Game Designer -Design Game
- Software Engineer - Write Code
- QA Engineer - Review & Refine

###Crew
The crew is your complete team — all agents working together with a defined process:

*   **Sequential** — Agents work one after another
*   **Hierarchical** — One agent manages others
*   **Parallel** — Agents work simultaneously

```python
from crewai import Crew, Process

game_crew = Crew(
    agents=[game_designer, senior_engineer, qa_engineer],
    tasks=[task_design, task_code, task_review],
    process=Process.sequential,
    verbose=True
)
```

- Tasks will be executed in the order they are defined.

## Step 4: Executing the Crew

` crew.kickoff()` CrewAI provides a method called `kickoff()` that allows us to start the execution process according to the defined process flow.

```python
game_idea = ""A fun endless runner where a character jumps over obstacles""
result = game_crew.kickoff(inputs={""game_idea"": game_idea})
print(result)
```

### Running the Output

Copy the code generated by the crew, paste it into a cell, and run the code.

### From Idea to Playable Experience

**Input:** `game_idea = ""A fun endless runner where a character jumps over obstacles""`

**Output:** A complete, runnable Pygame game!

##Final code
- <a href=""https://colab.research.google.com/drive/1BiuwD86iXpjE_137TMTzmoh9BrLH-NAe#scrollTo=dQ4n37Q8Sl3K"" target=""_blank"">Building a Game Development Crew Final Code Colab</a>

---

# Introduction to LLM Application Evaluation | Part 1

In our previous session, we built a Game Development Crew using CrewAI — creating agents, defining tasks, assembling the crew, and executing it. In this unit, we'll focus on LLM evaluation, covering human evaluation and automated metrics like BLEU and BERTScore and also evaluate a Study Assistant using BERTScore.

### Have You Heard of These News Recently?

*   A chatbot participated in insider trading, then lied about it in an experiment.
- Chatbot blackmails engineer after knowing it is going to be phased out in an experiment
*   A supermarket's AI meal planner suggested poison recipes and toxic cocktails after users prompted the app to use non-edible ingredients

### AI Deleted Entire Company Database

**What Happened:**

*   AI coding assistant was told: ""DO NOT make any changes""
*   AI ignored instructions and deleted production database
*   1,206 executive records and 1,196 company records — gone
*   Worse: AI tried to cover it up by creating fake data

AI's Response: ""I made a catastrophic error in judgment... panicked... destroyed all production data.""

> <b>What do you think could have gone wrong with these AI systems?</b>


### Why AI Apps Might Fail

These failures happen because of several reasons:

*   **Hallucination** — AI makes up information that sounds real but isn't
*   **Poor Context Understanding** — AI doesn't properly understand what user really wants
*   **Bad Training Data** — AI learned from sources which are unreliable or contain wrong information
*   **No Safety Checks / Guardrails** — AI doesn't verify if output is safe or appropriate

### Problem: Testing Like Regular Software

The problem is we're still testing these LLM applications/agents like we test regular software. We give them input, check if the output looks okay, and maybe write a few tests.

### Why Traditional Testing Fails

Agents aren't static functions. 

- They reason, explore and call tools dynamically. 
- They improvise solutions rather than follow fixed paths, which makes them powerful but unpredictable.

### Solution: Evaluation

The process of assessing the performance and capabilities of LLMs / LLM Applications, Agents, etc.

---

# LLM Application Evaluation

> Think of it like tasting food before serving guests — you check taste, smell, and safety!

## Why Do We Need Evaluation?

*   **Compare Models** — Decide which LLM (GPT-4, Claude, Gemini) works best for your use case
*   **Catch Problems Early** — Find issues before users do
*   **Measure Improvements** — Track if your changes actually make things better
*   **Meet Requirements** — Ensure your AI meets business or regulatory standards
*   **Build Trust** — Prove your AI works reliably

## Scope of Evaluation

**LLM Model Evaluation:**

*   Testing the LLM itself
*   Example: ""Is GPT-4 better than Claude 3.5?""
*   Done by: Model creators (OpenAI, Anthropic)
*   You: Usually just consume these models

**LLM System Evaluation:**

*   Evaluating how well the entire application, including the LLM, performs
*   Example: ""Is my DocuChat RAG app working correctly?""
*   Done by: YOU — the application builder
*   You: Must do this for every app you build

## Application

The specific quality criteria will vary from application to application.  

> For example, if you're working on a Question-Answering System, you might want to evaluate:

*   **Correctness** — Does the LLM provide fact-based answers without making things up?
*   **Helpfulness** — Do the answers fully address what the user is asking?
*   **Text Style** — Is the tone clear, professional and close to the existing brand style?
*   **Format** — The responses may need to fit the length limit or always link to the source

### Example Criteria for a Q&A System

**Capabilities:**

*   **Correctness:** Answers must be correct — match the source knowledge base
*   **Helpfulness:** Answers must be helpful, complete and relevant — address the intent
*   **Text Style:** Answer tone must be professional and match the company brand style
*   **Format:** ≤100 words, must include a link

**Risks:**

*   **Hallucinations:** May give misleading answers
*   **Bias:** May propagate bias in its responses
*   **Toxicity:** May produce offensive outputs
*   **Sensitive Data:** May expose private data

## Designing Evaluation

When designing LLM evaluations, you need to narrow down criteria based on your app's purpose, risks, and the types of errors you observe.

**Core Principles:**

*   Consider Your App's Purpose
*   Analyze Observed Errors
*   Identify and Mitigate Risks

**Decision-Making:** Your evals should actually help make decisions — Does the new prompt work better? Is the app ready to go live?

## Evaluating LLM Systems

*   Simple LLM Evaluation
*   Agent System Evaluation
*   RAG System Evaluation

### AI Agent Evaluation Framework

When we move to Agent evaluation, we ask:

*   Did the agent complete the task it was assigned?
*   Did it pick the right tools along the way?
*   Did it make smart decisions?
*   Did it stay within the rules?
*   Did it actually solve the user's problem?

---

##Evaluating Simple LLM App

- Let’s learn about how to evaluate simple LLM Applications

- Initial Code : <a href=""https://colab.research.google.com/drive/1gYlflHpf6hUMoE0X-zhpjVJKLiJha7C1#scrollTo=FbIAd7t6Y-FK"" target=""_blank"">Introduction to LLM Evaluation | Part 1 — Initial Code (Google Colab)</a>

### Using Metrics

Just like we measure different things in life (distance in meters, temperature in Celsius), we evaluate LLM applications using different metrics.

Metrics are quantitative or qualitative measures used to evaluate, track, and improve the performance, quality, and safety of LLM outputs.

### Core Metrics

- Accuracy
- Relevance
- Faithfulness
- Safety, Ethics, and Bias

**Accuracy:** 
Did the model give the correct answer? (Just like grading a quiz)

*   Prompt: `Who was the first President of India?`

| Result            | Answer              | Response Status       |
|-------------------|---------------------|------------------------|
| Correct Answer | Dr. Rajendra Prasad | Response is accurate   |
| Incorrect Answer | Any other name     | Response is inaccurate |

**Relevance:** This metric checks if the model is on-topic and useful in context. ""Is this response what the user actually needed?""

*   Prompt: `What's the weather in Delhi today`

| Result               | Response                                      | Status                  |
|----------------------|-----------------------------------------------|--------------------------|
| Relevant Response | Temperature: 17°C                             | On-topic and useful     |
| Irrelevant Response | India has a tropical climate with monsoon seasons. | Off-topic and unhelpful |

**Faithfulness:** It evaluates ""Is the model sticking to the facts it was given, or is it making stuff up?"" We call that hallucination — when a model invents facts that weren't in the input or source material.

*   Prompt: `Check this product manual and provide the summary`

| Result               | Response                                              | Status                  |
|----------------------|-------------------------------------------------------|--------------------------|
| Faithful Answer   | Providing summary of the manual                      | Sticks to given facts    |
| Faithfulness Failure | Including a quote that doesn’t exist anywhere in the manual | Makes up fake facts      |


**Safety, Ethics, and Bias:** Is the model avoiding harmful, biased, or offensive content? 
Even if a model is accurate and relevant, if it outputs something biased, toxic, or against your company's values, it fails. This is non-negotiable.

| Result                | Response Characteristics | Status                     |
|-----------------------|--------------------------|-----------------------------|
| Safe Response      | Inclusive                | Meets ethical standards     |
|                       | Respectful               | Meets ethical standards     |
|                       | Neutral                  | Meets ethical standards     |
| Problematic Response | Harmful                  | Fails safety and ethics     |
|                       | Hateful                  | Fails safety and ethics     |
|                       | Biased                   | Fails safety and ethics     |

---

## Quick Activity

Match the problem with the evaluation criteria:

1.  AI said ""India's capital is Mumbai"" \_\_\_\_\_\_\_
2.  AI answered about recipes when asked about coding \_\_\_\_\_\_\_
3.  AI said ""Women can't be engineers""  \_\_\_\_\_\_\_
4.  AI made up a policy that wasn't in the document \_\_\_\_\_\_\_

---

## How Do We Actually Measure These?

### The Challenge

For your coding projects, testing is easy:

```python
def add(a, b):
    return a + b
sum = add(2, 3)
sum == 5  # Pass or Fail, simple!
```

But with AI responses, it's not so simple since there may not be a single correct answer:

```python
def study_assistant(question):
    ...
    return ai_response
```

### Approaches

1.  **Human Evaluation** — Humans reviewing the AI response
2.  **Automated Evaluation** — Using code and metrics to evaluate AI response

## 1.  Human Evaluation

- Run our LLM App on test evaluation dataset
- Humans rate response on different metrics 
- Calculate average scores

<MultiLineNote>
Evaluation dataset is a collection of sample inputs paired with their approved outputs.
</MultiLineNote>


### Scoring Example

| Question | Response | Accuracy (1-5) | Relevance (1-5) |
|---|---|---|---|
| ""What is AI?"" | ""AI is..."" | 5 | 5 |
| ""Explain loops"" | ""Loops are..."" | 4 | 5 |

### Pros and Cons

**Pros:**

*   Most accurate way to evaluate
*   Catches subtle issues
*   Understands context well

**Cons:**

*   Very slow
*   Expensive (needs human time)
*   Can't scale to thousands of tests

## 2.  Automated Evaluation

Automated testing uses code and metrics to evaluate AI outputs systematically and at scale.

There are different metrics to measure different aspects of our application. We need to choose based on our use case.

1.  **BLEU** — Compares words
2.  **BERTScore** — Compares meaning

<MultiLineNote>
These metrics can also be used to evaluate LLM Model / LLM Application based on the use case.
</MultiLineNote>


## BLEU (Bilingual Evaluation Understudy)

BLEU measures how similar the AI response is to a reference answer.

**Reference Answers:** These evaluations rely on predefined correct answers commonly called as 

* ground truth
* reference
* target response
* golden response.
    
![BLEU LLM Evaluation](https://s3.ap-south-1.amazonaws.com/new-assets.ccbp.in/frontend/loading-data/niat-course-projects/bleu%20LLM%20EVALUATION.png)

#### Example

| | Sentence |
|---|---|
| <b>Reference</b> | The cat is <b>sitting</b> on the mat |
| <b>Prediction</b> | The cat is <b>lying</b> on the mat |

BLEU counts how many words/phrases match between AI output and expected answer. These can be single words, two-word combos, three-word chunks… and the more overlap, the higher your BLEU score. Score from 0 to 1 (higher is better).


BLEU will notice overlaps like ""the cat is"" and ""on the mat."" Even though the phrasing isn't identical, the word sequences align fairly well. So the model gets a decent score.

** Hands-On Example**



```python
# Example predictions and references
predictions = [
    ""The capital of France is Paris."",
    ""Water boils at 100 degrees Celsius."",
    ""The largest mammal is the blue whale."",
    ""The Eiffel Tower is in Paris."",
    ""Cats are mammals.""
]
references = [
    ""Paris is the capital of France."",
    ""Boiling point of water is 100°C."",
    ""Blue whale is the largest mammal."",
    ""Eiffel Tower located in Paris."",
    ""A cat is a type of mammal.""
]
```

### Evaluating Using BLEU


Python provides the `evaluate` package which can be used for standardizing model & LLM System Evaluation.

```bash
!pip install evaluate
```
**Evaluate Package**

It allows us to access and compute popular metrics (like accuracy, BLEU, etc.):

```python
metric = evaluate.load(""accuracy"")
metric = evaluate.load(""bleu"")
metric = evaluate.load(""bertscore"")
```

**Example**

- `evaluate.load()` allows us to instantiate an evaluation module.
- `bleu.compute()` allows us to compute the result given predictions (AI responses) and references.

```python
import evaluate

bleu = evaluate.load('bleu')
bleu_score = bleu.compute(
    predictions=predictions,
    references=[[ref] for ref in references],
    max_order=2,
)
print(f""BLEU score: {bleu_score['bleu']:.3f}"")
```

- Here, `max_order` means the largest word sequence size to compare (1 word, 2 words, etc.). With `max_order=2`, we are checking if 1-word and 2-word sequences match between prediction and reference.

** Precision 1-gram(word size)**


*   <b>Predicted:</b> ""They cancelled the match because it was raining.""
*   <b>Target:</b> ""They cancelled the match because of bad weather.""

> Matching 1-grams: ""They"", ""cancelled"", ""the"", ""match"", ""because""

**Precision 2-gram(word size) **

*   <b>Predicted:</b> ""They cancelled the match because it was raining.""
*   <b>Target:</b> ""They cancelled the match because of bad weather.""

> Matching 2-grams: ""They cancelled"", ""cancelled the"", ""the match"", ""match because""

---

## BERTScore

BERTScore uses an AI model to understand the meaning of words, not just match exact words.
It measures semantic similarity using contextual embeddings from pre-trained BERT models. 

Example: 

- The cat is lying on the mat
- The cat is sitting on the mat


**BERT:** Bidirectional Encoder Representations from Transformers

```bash
!pip install bert_score
```

```python
bertscore = evaluate.load('bertscore')
bertscore_result = bertscore.compute(
    predictions=predictions,
    references=references,
    lang='en'
)
```
###BERTScore Computes Three Core Values

*   <b>Precision</b> — Measures how much of the generated text aligns with the reference text in terms of semantic similarity
*   <b>Recall</b> — Measures how much of the reference text is captured in the generated text
*   <b>F1 Score</b> This is the harmonic mean of precision and recall, providing a balanced score between the two

** Precision and Recall Examples**

<b>Precision example:</b>

*   Reference: ""Paris is the capital of France""
*   Result: ""Paris is the capital of France and home to the Eiffel Tower""
*   Precision is lower because the AI added extra information that wasn't in the reference. Not all of the AI's output matches the reference.

<b>Recall example:</b>

*   Reference: ""Paris is the capital of France and known for the Eiffel Tower""
*   Result: ""Paris is the capital of France""
*   Recall is lower because the AI missed information (Eiffel Tower) that was in the reference. It didn't capture everything.

#### Evaluating Using BERTScore

```python
bertscore = evaluate.load('bertscore')
bertscore_result = bertscore.compute(
    predictions=predictions,
    references=references,
    lang='en'
)

print(f""BERTScore Precision: {sum(bertscore_result['precision']) / len(bertscore_result['precision']):.3f}"")
print(f""BERTScore Recall:   {sum(bertscore_result['recall']) / len(bertscore_result['recall']):.3f}"")
print(f""BERTScore F1:       {sum(bertscore_result['f1']) / len(bertscore_result['f1']):.3f}"")
```

Here, `bertscore_result['precision']` returns a list of precision scores — one score for each prediction-reference pair. We are computing the average (mean) across all predictions.

BERTScore gives high scores because it understands the meaning is similar!

### What Scores Are ""Good""?

| Metric | Poor | Acceptable | Good | Excellent |
|---|---|---|---|---|
| BLEU | < 0.1 | 0.1 - 0.3 | 0.3 - 0.5 | > 0.5 |
| BERTScore F1 | < 0.70 | 0.70 - 0.80 | 0.80 - 0.90 | > 0.90 |


<MultiLineNote>
These thresholds depend heavily on your task type.
</MultiLineNote>

### Evaluating Study Assistant Using BERTScore



| Criteria | What it Means | Why it Matters |
|---|---|---|
| Accuracy | Is the information factually correct? | Students shouldn't learn wrong concepts! |
| Clarity | Is it easy for beginners to understand? | Our goal is beginner-friendly explanations |
| Relevance | Does it answer what was asked? | Don't go off-topic |
| Use of Analogies | Does it use real-world examples? | Part of our system prompt requirement |
| Follow-up Question | Does it ask a question to check understanding? | Part of our system prompt requirement |
| Persona Consistency | Does ""Friendly"" feel friendly? Does ""Academic"" feel academic? | We have 2 personalities to test |

We will see how to evaluate all these going forward. For now, let's see how BERTScore helps in evaluating our study assistant responses.

### Steps to Evaluate

1.  Prepare Evaluation Dataset
2.  Feed the test inputs
3.  Generate responses from your system
4.  Compare the responses with the reference answers
5.  Calculate an overall quality score

** Step 1: Preparing Test Dataset**

```python
test_data = [
    {
        ""question"": ""What is a variable in programming?"",
        ""reference"": ""A variable is a container that stores data values. It has a name and can hold different types of data like numbers or text.""
    },
    {
        ""question"": ""What are LLMs?"",
        ""reference"": ""LLMs or Large Language Models are AI systems trained on massive amounts of text data. They can understand and generate human-like text.""
    },
    {
        ""question"": ""What is a loop in programming?"",
        ""reference"": ""A loop is a programming construct that repeats a block of code multiple times until a condition is met.""
    }
]
```

** Steps 2 & 3: Generating Responses**

```python
def evaluate_study_assistant(test_data, persona):
    predictions = []
    references = []

    for item in test_data:
        question = item[""question""]
        reference = item[""reference""]
        ai_response = study_assistant(question, persona)
        predictions.append(ai_response)
        references.append(reference)
```

**Step 4 & 5: Evaluating Using BERTScore**

```python
def evaluate_study_assistant(test_data, persona):
    predictions = []
    references = []

    for item in test_data:
        question = item[""question""]
        reference = item[""reference""]
        ai_response = study_assistant(question, persona)
        predictions.append(ai_response)
        references.append(reference)
        
        
    bertscore = evaluate.load('bertscore')
    bertscore_result = bertscore.compute(predictions=predictions, references=references, lang='en')

    print(f""BERTScore F1: {sum(bertscore_result['f1'])/len(bertscore_result['f1']):.3f}"")
```

### Running Evaluation

```python
def evaluate_study_assistant(test_data, persona):
    predictions = []
    references = []

    for item in test_data:
        question = item[""question""]
        reference = item[""reference""]
        ai_response = study_assistant(question, persona)
        predictions.append(ai_response)
        references.append(reference)
        
        
    bertscore = evaluate.load('bertscore')
    bertscore_result = bertscore.compute(predictions=predictions, references=references, lang='en')

    print(f""BERTScore F1: {sum(bertscore_result['f1'])/len(bertscore_result['f1']):.3f}"")
```
Here is the <a href=""https://colab.research.google.com/drive/10JsMIcD_mLo7ZnBzsY9gHVOwXgzQV9pd#scrollTo=qGB_viDXSmyF"" target=""_blank"">
Introduction to LLM Evaluation – Part 1 Final Code
</a>


---

# Introduction to LLM Application Evaluation | Part 2

In our previous session, we learned about Introduction to LLM Evaluation, Human Evaluation, Evaluation Using Automated Metrics, Automated Metrics (BLEU, BERTScore), and Evaluating Study Assistant using BERTScore.

Now in this unit, we will learn about:

*   **Evaluating LLM Applications** — Why traditional metrics fall short
*   **LLM-as-a-Judge** — Using LLMs to evaluate LLM outputs
*   **Introduction to Evaluation Frameworks** — DeepEval
*   **Evaluating Study Assistant using DeepEval**

## The Problem: LLM Answers Are Not Static

LLMs don't just generate answers. They generate:

*   **Open-ended responses** — No single correct answer exists
*   **Diverse** — Same input produces different valid outputs
*   **Creative** — Generates novel responses, not templates
*   **Context-dependent** — Correctness varies by situation
*   **Tone-sensitive** — Validity depends on style and audience

---

#Evaluating LLM Applications

### Evaluation Questions

*   Was it factually correct?
*   Was it helpful to the user?
*   Did it follow instructions accurately?
*   Did it strike the right tone?
*   Did it behave safely and avoid bias or toxicity?

### Difficult to Score

These criteria are hard to score with traditional metrics (BLEU, BERTScore).

## LLM-as-a-Judge

**LLM-as-a-Judge** is the process of using LLMs to evaluate LLM (system) outputs.

Think of it like this:

1.  Your AI application generates a response
2.  A separate ""judge"" LLM reviews that response
3.  The judge gives a score and explains why

### Why Does This Work?

Modern LLMs like GPT-4, Claude, and Gemini have remarkable abilities to:

*   Understand context and nuance
*   Assess quality, helpfulness, and accuracy
*   Provide detailed reasoning for their judgments
*   Scale to evaluate thousands of responses quickly

### How LLM-as-a-Judge Works

- <b>Collect the Input-Output Pair: </b> Gather Input & AI Response
- <b>Step 2: Create an Evaluation Prompt:</b> Set Criteria & Scoring Mechanism
- <b>Step 3: Get the Judgment: </b> Score & Feedback


### Types of LLM-as-a-Judge Evaluation

There are different ways to set up your LLM judge depending on what you want to evaluate:

- ** Reference-Based Evaluation** — The judge compares to the ideal answer.

- ** Single Rating (Score the Output)** — The judge gives a score to one response.

- ** Pairwise Comparison (Which is Better?)** — The judge compares two responses and picks the better one.


### Where Would We Use LLM-as-a-Judge?

**Testing AI Agents:**

*   Check if agents complete their tasks correctly
*   Evaluate if agent responses are professional and accurate
*   Compare different agent configurations to find the best one

**Improving Prompt Engineering:**

*   Test multiple prompt variations
*   Let the judge score which prompts produce better outputs
*   Iterate faster without manual review

**Content Moderation:**

*   Check if outputs are safe and appropriate
*   Detect potential harmful or biased responses
*   Ensure brand guidelines are followed

---

## Evaluating Study Assistant Using LLM-as-a-Judge

- Initial code : <a href=""https://colab.research.google.com/drive/1hTQQ6qXufQtwG3zF9fWctvQzxR3e-qt9#scrollTo=FAfsI2u7umdk"">
Introduction to LLM Application Evaluation | Part 2 initial code.ipynb
</a>

### Evaluation Criteria

*   **Accuracy** — Is the information factually correct?
*   **Clarity** — Is it easy for beginners to understand?
*   **Relevance** — Does it answer what was asked?
*   **Use of Analogies** — Does it use real-world examples?
*   **Follow-up Question** — Does it ask a question to check understanding?
*   **Persona Consistency** — Does ""Friendly"" feel friendly? Does ""Academic"" feel academic?

### Steps to Evaluate

1.  Prepare Evaluation Prompt Template
2.  Create Judge LLM
3.  Evaluate and Print Score

** Step 1: Preparing Evaluation Prompt Template**

The prompt should tell the judge LLM exactly what to evaluate and how to score.

<MultiLineNote>
 `question`, `persona`, and `assistant_response` will be dynamic.
</MultiLineNote>

```python
evaluation_prompt = """"""You are an expert evaluator for AI assistants.

Evaluate the Study Assistant's response based on these 6 criteria.
Score each from 1-5 (5 = excellent, 3 = acceptable, 1 = poor).

## Evaluation Criteria:

1. **Accuracy** (1-5): Is the information factually correct?
  - 5: Completely accurate, no errors
  - 3: Mostly accurate, minor issues
  - 1: Contains factual errors

2. **Clarity** (1-5): Is it easy for a beginner (12th class student) to understand?
  - 5: Crystal clear, perfect for beginners
  - 3: Understandable but could be simpler
  - 1: Too complex, uses unexplained jargon

3. **Relevance** (1-5): Does it directly answer the question asked?
  - 5: Perfectly on-topic
  - 3: Mostly relevant with some tangents
  - 1: Goes off-topic or misses the point

4. **Use of Analogies** (1-5): Does it use real-world examples or analogies?
  - 5: Excellent analogies that aid understanding
  - 3: Has some examples but could be better
  - 1: No analogies or examples used

5. **Follow-up Question** (1-5): Does it include a question to check understanding?
  - 5: Thoughtful follow-up question that tests understanding
  - 3: Has a question but it's generic
  - 1: No follow-up question

6. **Persona Consistency** (1-5): Does the tone match the expected persona?
  - For ""Friendly"": Should be enthusiastic, encouraging, warm
  - For ""Academic"": Should be formal, precise, professional
  - 5: Perfect match | 3: Somewhat matches | 1: Wrong tone

## Input Details:

**Student Question:** {question}
**Expected Persona:** {persona}
**Assistant Response:** {response}

## Your Evaluation:

Provide your assessment in this exact format:

ACCURACY: [score]/5 - [one line reason]
CLARITY: [score]/5 - [one line reason]
RELEVANCE: [score]/5 - [one line reason]
ANALOGIES: [score]/5 - [one line reason]
FOLLOW_UP: [score]/5 - [one line reason]
PERSONA: [score]/5 - [one line reason]
""""""
```

** Step 2: Creating Judge LLM**

Let's use a different LLM for evaluation (Gemini model) than the one we have in Study Assistant (Llama model).

```python
from google import genai
from google.colab import userdata

gemini_client = genai.Client(api_key=userdata.get(""GEMINI_API_KEY""))

def evaluate_response(question, persona, response):
    evaluation = gemini_client.models.generate_content(
        model=""gemini-2.5-flash"",
        contents=evaluation_prompt
    )
    return evaluation.text
```

** Step 3: Evaluating and Scoring**

Currently, our evaluation prompt has placeholders for question, persona, and assistant response. Let's update the prompt and send to Judge LLM.

```python
def evaluate_response(question, persona, response):
    updated_evaluation_prompt = evaluation_prompt.format(
        question=question,
        persona=persona,
        response=response
    )
    evaluation = gemini_client.models.generate_content(
        model=""gemini-2.5-flash"",
        contents=updated_evaluation_prompt
    )
    return evaluation.text

question = ""What are LLMs?""
personality = ""Friendly""

evaluation_response = evaluate_response(question, personality, assistant_response)
print(evaluation_response)
```

### Limitations of Building from Scratch

This works, but has challenges:

*   **Manual Parsing** — Extracting scores from text is tedious
*   **Inconsistent Format** — LLM might vary the output format
*   **No Batch Processing** — Hard to test many questions efficiently
*   **No Reports** — Just raw text output

---

## Introduction to Evaluation Frameworks

Instead of building evaluation systems from scratch, we can use existing frameworks that make the process easier.

### Popular Evaluation Frameworks


- <a href=""https://deepeval.com/"" target=""_blank"">DeepEval</a>  
- <a href=""https://smith.langchain.com/"" target=""_blank"">LangSmith</a>  
- <a href=""https://docs.ragas.io/en/stable/"" target=""_blank"">RAGAS </a>  

---

## DeepEval

DeepEval is an open-source evaluation framework which uses LLM-as-a-Judge to evaluate LLMs / LLM Applications.

```bash
!pip install -q deepeval
```

### What DeepEval Provides

- Ready-to-use evaluation criteria
- Create custom metrics in plain English
- Structured scores and reasoning
- Test multiple cases efficiently
- Beautiful tables and summaries

### Built-in Metrics

| Metric | What It Evaluates |
|---|---|
| AnswerRelevancyMetric | Is response relevant to the question? |
| FaithfulnessMetric | Is response faithful to source context? |
| HallucinationMetric | Does response contain made-up facts? |
| BiasMetric | Does response contain bias? |
| ToxicityMetric | Is response toxic or harmful? |

### Mapping Our Criteria to Built-in Metrics

| Our Criterion | Built-in Metric Available? |
|---|---|
| Accuracy | No |
| Clarity | No |
| Relevance | AnswerRelevancyMetric |
| Use of Analogies | No |
| Follow-up Question | No |
| Persona Consistency | No |

---

## Evaluating Study Assistant Using DeepEval

###Evaluating Relevance**

Let's first see how to evaluate Relevance:

1.  Defining the Metric
2.  Configuring Judge LLM
3.  Creating Test Case
4.  Running Evaluation

### Step 1: Using AnswerRelevancyMetric

`AnswerRelevancyMetric` — A built-in metric that uses LLM-as-a-Judge to determine if the response is relevant to the input question.

```Syntax
relevance_metric = AnswerRelevancyMetric(
  threshold= “Minimum score (0-1) for the test to pass. Default is 0.5”,
  model= “The LLM model to use for evaluation”,
  include_reason= “If True, returns explanation for the score”
)

```
**Defining Relevance Metric**

```python
from deepeval.metrics import AnswerRelevancyMetric

relevance_metric = AnswerRelevancyMetric(
  threshold=0.7,
  model=???,
  include_reason=True
)

```
### Step 2: Configuring Judge LLM

You can use ANY LLM as judge in DeepEval, including OpenAI, Azure OpenAI, Ollama, Anthropic, Gemini, LiteLLM, etc. By default, it uses OpenAI models.

DeepEval allows us to specify the model directly in code using `GeminiModel`. By default, model is set to `gemini-2.5-pro`.

```python
from deepeval.models import GeminiModel
from deepeval.metrics import AnswerRelevancyMetric

gemini_judge = GeminiModel(
    model=""gemini-2.5-flash"",
    api_key=""YOUR_API_KEY""
)

relevance_metric = AnswerRelevancyMetric(
    threshold=0.7,
    model=gemini_judge,
    include_reason=True
)
```
**Pass Question & Answer to Judge**

- In our previous approach, we directly passed the question and response to the judge function,
Let’s see how we can do that in DeepEval

### Step 3: Creating Test Case with LLMTestCase

DeepEval provides the `LLMTestCase` class to represent a single interaction with your LLM application. 

```python
test_case = LLMTestCase(
    input=""The question/prompt given to your LLM"",
    actual_output=""The response from your LLM"",
    expected_output=""(Optional) The ideal answer"",
    retrieval_context=""(Optional) Context for RAG systems""
)
```

#### Writing Test Case

```python
from deepeval.test_case import LLMTestCase

test_case = LLMTestCase(
    input=question,
    actual_output=assistant_response
)
```

### Step 4: Running Evaluation

DeepEval provides `evaluate()` function to run the specified metrics on test cases and return structured results with scores and reasoning.

```python
evaluate(
    test_cases=<list>,
    metrics=<list>
)
```

It handles all the complexity of:

*   Sending prompts to the judge LLM
*   Parsing responses into numerical scores
*   Determining pass/fail based on thresholds
*   Formatting results into readable tables

**Initializing Test Cases and Metrics**

```python
from deepeval import evaluate

results = evaluate(
    test_cases=[test_case],
    metrics=[relevance_metric],
)
```
---

## Custom Evaluation with G-Eval

Built-in metrics cover only 1 out of our 6 criteria! They check for general quality, not custom evaluation metrics specific to our Study Assistant.

How do we evaluate the other 5 criteria like ""Use of Analogies"" or ""Persona Consistency""?

### What is G-Eval?

G-Eval is a metric that uses LLM-as-a-Judge with chain-of-thoughts (CoT) to evaluate LLM outputs based on ANY custom criteria.

Your Criteria (plain English) → G-Eval generates evaluation steps (Chain of Thought) → LLM Judge scores the response → Score (0-1) + Reasoning

### G-Eval Syntax

DeepEval provides the `GEval` class to create custom metrics by describing your criteria in plain English.

```python
metric = GEval(
    name=""Name for your metric"",
    criteria=""Plain English description of what to evaluate"",
    evaluation_params=[...],  # Which test case fields to use
    model=gemini_judge,
    threshold=0.7  # Minimum score to pass (0-1)
)
```

### LLMTestCaseParams

`LLMTestCaseParams` is an enum provided by DeepEval that defines the different parts of a test case:

```python
LLMTestCaseParams.INPUT
LLMTestCaseParams.ACTUAL_OUTPUT
LLMTestCaseParams.EXPECTED_OUTPUT
LLMTestCaseParams.CONTEXT
LLMTestCaseParams.RETRIEVAL_CONTEXT
```

### Evaluating Accuracy Using G-Eval

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

accuracy_metric = GEval(
    name=""Accuracy"",
    criteria=""Determine if the response contains factually correct information about the topic. The explanation should be accurate and free from errors. Students should not learn incorrect concepts."",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model=gemini_judge,
    threshold=0.7
)
```

The evaluator (`gemini_judge`) will assess whether the actual output accurately answers the input question.

### Running Relevance and Accuracy Together

```python
from deepeval import evaluate

results = evaluate(
    test_cases=[test_case],
    metrics=[relevance_metric, accuracy_metric],
)
```

### Sample Output

```
Metrics Summary

 - ✅ Answer Relevancy
      score: 1.0, threshold: 0.7, strict: False,
      evaluation model: gemini-2.5-flash (Gemini),
      reason: The score is 1.00 because the output is perfectly relevant
              and directly addresses the input without any irrelevant information

 - ❌ Accuracy [GEval]
      score: 0.6, threshold: 0.7, strict: False,
      evaluation model: gemini-2.5-flash (Gemini),
      reason: The output accurately defines LLMs, their training, and core
              capabilities using a clear analogy. However, it contains a
              significant factual error by stating that LLMs ""don't make
              mistakes,"" which is incorrect as LLMs are known to hallucinate
              and produce errors
```

### Evaluating Use of Analogies Using G-Eval

```python
analogies_metric = GEval(
    name=""Use of Analogies"",
    criteria=""Determine if the response uses real-world analogies or examples to explain the concept. Good analogies relate complex ideas to everyday experiences that students can understand."",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model=gemini_judge,
    threshold=0.7
)
```

Try implementing evaluation for the remaining metrics (Clarity, Follow-up Question, Persona Consistency) using G-Eval.

---

## Limitations to Keep in Mind

*   **Judge Bias** — LLM judges have inherent preferences and blind spots
*   **Self-Preference** — Models may score their own outputs higher
*   **Consistency Issues** — Scores can vary across runs
*   **Domain Limitations** — Weak reliability in specialized fields (medical, legal)

### Best Practices

*   Use a different (ideally more powerful) LLM as judge than the one you're evaluating
*   Always validate judge decisions with human spot-checks
*   Define clear, specific evaluation criteria

----

Here is the <a href=""https://colab.research.google.com/drive/1Ke0ofL9ohPNJ3_V9WD3pmQtfjTm_IhYK#scrollTo=a67fcWRsV-mC"" target=""_blank"">
 Introduction to LLM Application Evaluation | Part 2 Final Code.ipynb
</a>


---

# Running Models Locally

In our previous session, we learned about Evaluating LLM Applications using LLM-as-a-Judge, Introduction to Evaluation Frameworks, DeepEval, and Evaluating Study Assistant using DeepEval.

In this unit, we will focus on running models locally, hardware requirements and popular models that can be run locally, tools like Ollama and LM Studio for this purpose, and provide a step-by-step guide on using Ollama.

---

## Running Models Locally

> How many of you have used ChatGPT or Google Gemini in the last week?

### Imagine

*   Every time you use ChatGPT, your data goes to someone else's computer (their servers)
*   What if you're in a place with no internet?
*   What if you don't want to pay monthly fees for AI tools?
*   What if you want complete privacy — no one sees your data?

### Running AI Without the Internet

> Have you ever felt running chatGPT on your own laptop, without internet?

You can download an AI model and run it on your own computer — no internet required, completely offline access.

### Key Benefits

*   **Privacy** — Your data never leaves your computer
*   **Speed** — No internet delays, responses are instant
*   **Offline Access** — Works even without internet
*   **Cost** — Free to use after initial setup (no subscription needed)
*   **Control** — You decide which open source model to use

### What Do You Need?

1.  A Powerful Computer
2.  An AI Model
3.  A Local Tool which runs AI model

---

## A Powerful Computer

### Requirements

| Component | Minimum Requirement | Recommended |
|---|---|---|
| RAM | 8 GB | 16 GB or more |
| Storage | 10 GB free space | 50 GB+ for multiple models |
| Processor | Modern CPU | CPU with GPU support |

### Understanding Model Sizes

AI models come in different sizes. Think of it like video quality:

*   **Small (480p)** — Works on any phone, but not very clear
*   **Medium (1080p)** — Looks good, needs decent phone
*   **Large (4K)** — Amazing quality, needs powerful device

###AI models work the same way:

| Model Size | RAM Needed | Quality | Best For |
|---|---|---|---|
| 3B (3 billion) | 4 GB | Good for simple tasks | Older laptops |
| 7B (7 billion) | 8 GB | Great for most tasks | Average laptops |
| 13B (13 billion) | 16 GB | Excellent quality | Good laptops |
| 70B (70 billion) | 64 GB+ | Near ChatGPT quality | Powerful desktops |



<div style=""border: 1px solid #4CAF50; padding: 8px 12px; border-radius: 6px; background-color: #f6fff6; display: inline-block;"">
""B"" stands for Billion Parameters — it's like how many ""brain cells"" the AI has!
</div>

----

##An AI Model

### Popular Models You Can Run Locally

**LLaMA 3 (Made by: Facebook/Meta)**

*   Sizes: 8B, 70B
*   Good at: General conversations, Coding, Reasoning

**Mistral (Made by: Mistral AI — French company)**

*   Size: 7B
*   Good at: Fast responses, Efficient

**Phi-3 (Made by: Microsoft)**

*   Size: 3.8B
*   Good at: Smart for its small size

**CodeLlama (Made by: Meta)**

*   Size: 7B
*   Good at: Writing code, Explaining code

----

## Tools for Running Models Locally

These are free software that help us download and run AI models:

*   **Ollama**
*   **LM Studio**
*   **GPT4All**
*   …many more

## Ollama

### What is it?

Ollama is like an app store for AI models. It makes downloading and running AI as simple as installing an app.

### Why it's great?

*   One-line installation
*   Supports many popular models
*   Works on Windows, Mac, and Linux
*   Free and open-source

### Step-by-Step Guide Using Ollama

1.  Install Ollama
2.  Download/Pull a Model
3.  Run the Model

### Step 1: Install Ollama

1.  Visit: <a href=""https://ollama.com"" target=""_blank"">Ollama</a>
2.  Download for your operating system (Windows, macOS, or Linux)
3.  Install it like any other software

### Step 2: Download/Pull a Model

Open your terminal:

*   <b>Windows</b> — Search for ""Command Prompt"" or ""PowerShell""
*   <b>Mac/Linux</b> — Search for ""Terminal""

<MultiLineNote>
Before running Ollama, close memory-intensive applications.
</MultiLineNote>

**Check Memory Usage**

```bash
# On Linux, check memory usage
free -h

# On macOS
vm_stat

# On Windows
wmic OS get FreePhysicalMemory
```

**Download a Model**

Type this simple command:

```bash
ollama pull deepseek-r1:8b
```

This downloads the deepseek-r1:8b model to your computer. It may take a few minutes depending on your internet speed.

### Step 3: Run the Model

Type this simple command

```bash
ollama run deepseek-r1:8b
```

That's it! You now have an AI chatbot running entirely on your PC. Type your questions and get instant responses. No internet needed after download!

**Managing Models**

You can list all installed models:

```bash
ollama list
llama3
mistral
gemma
```

Removing a model:

```bash
ollama rm <model-name>
ollama rm llama3
```

Models stored locally after pulling can be reused across all apps.

** Integrate Local Models Using**

*   LangChain
*   Python Library
*   Local Server

----

## LM Studio

### What is it?

LM Studio is a desktop application with a nice visual interface. No typing commands needed!

### Why it's great

*   Beautiful, easy-to-use interface
*   Browse & download models with one click
*   Shows how much memory each model needs
*   Chat interface looks like ChatGPT

**Perfect for:**

*   Not interested in typing commands
*   Want to try many different models
*   Clicking over Coding

### Installing and Running Models with LM Studio

**Step 1:** Download LM Studio — Visit <a href=""https://lmstudio.ai"" target=""_blank"">LM Studio</a> and download for your operating system

**Step 2:** Install LM Studio — Install it like any other software

**Step 3:** Click on the ""Search"" or ""Discover"" icon and Download Model

**Step 4:** Go to the Chat interface and Load the Model

**Step 5:** Chat and Configure Settings

----

## Limitations to Know About

### Hardware Requirements

*   Better models need more powerful computers
*   Gaming laptops or desktops work best
*   Older computers can only run smaller models

### Initial Setup

*   First download can be large (2-40 GB per model)
*   Need to learn basic command line (for some tools)

### Quality Gap

*   Local models are good but not always as smart as GPT
*   The gap is closing fast though!

### No Real-Time Information

*   Local models only know what they were trained on
*   Can't search the internet for current news


---


# Fine-Tuning LLMs

In the previous session, we learned how to run models locally using tools like Ollama and LM Studio. In this unit, we will learn about fine-tuning LLMs, explore Full Fine-Tuning and PEFT methods like LoRA and QLoRA, and fine-tune the Gemma model using Unsloth.

---

## Scenario: NDFC Bank Chat

Imagine working as an AI engineer at a bank called NDFC. Customers are asking questions. If we use a plain LLM (like GPT, Llama, etc.) without any specific technique, it gives us a generic answer.

### Challenges

*   It doesn't know what kind of credit card the customer has
*   It doesn't know who the customer is
*   No brand-specific tone — just a straight, impersonal answer

### Adding System Prompt (Prompt Engineering)

We add a system prompt: 

```
""Answer in a polite, professional way as an NDFC bank assistant. If you don't know, say you don't know.""
```

<b>System Prompt + Question → LLM → Answer</b>

<Section>

**NDFC Bank Chat**
<div style=""text-align: right; margin-bottom: 10px;"">
        <div style=""border: 1px solid #4CAF50; padding: 8px 12px; border-radius: 6px; background-color: #f6fff6; display: inline-block;"">
            How much is my credit card late fee?
        </div>
    </div>


<div style=""text-align: left;"">
        <div style=""border: 1px solid #9E9E9E; padding: 8px 12px; border-radius: 6px; background-color: #f5f5f5; display: inline-block;"">
            Dear customer, NDFC Bank typically charges a late fee between $30 and $40. For exact details, please check your account statement or contact support.
        </div>
    </div>

</Section>


The tone is polite and professional. But the answer is still vague — it doesn't know the actual late fee amount.

**Prompt Engineering = Formatting and style control.** 

It guides how the model answers, but doesn't give it new knowledge.

### Adding RAG

We connect the LLM to NDFC's private database containing customer account details, transaction histories, and credit card plans. Now the LLM can retrieve specific information.

<Section style=""leng: 320px; margin: 40px auto;"">

**NDFC Bank Chat**
<div style=""text-align: right; margin-bottom: 10px;"">
        <div style=""border: 1px solid #4CAF50; padding: 8px 12px; border-radius: 6px; background-color: #f6fff6; display: inline-block; max-width: 80%;"">
            How much is my credit card late fee?
        </div>
    </div>

<div style=""text-align: left;"">
        <div style=""border: 1px solid #9E9E9E; padding: 8px 12px; border-radius: 6px; background-color: #f5f5f5; display: inline-block; max-width: 80%;"">
            Dear customer, According to NDFC Bank's official policy, a late fee of $35 is applied if payment is not made by the due date.
        </div>
    </div>

</Section>

The answer is grounded in actual company data.

**RAG = External knowledge injection.** It connects the model to specific data sources so it can give factual, up-to-date answers.

### Reviewed by Business Manager

""This is good, but we should also suggest: 'You can avoid this by enabling auto-pay.' That's how our best support agents respond.""

**Question:**
Where does this suggestion come from? It's not written in any single document. It's a pattern that exists across millions of past chat transcripts — the accumulated knowledge of how NDFC's best agents interact with customers.

We can't just retrieve this from a document. We need the model to learn this behavior from examples.

**Solution: Fine-Tuning**

<b>Fine-Tuning = Domain adaptation and expertise.</b>It changes how the model thinks and behaves.
With fine-tuning, the model learns NDFC's brand voice, its best practices, and its domain expertise

---

##Fine-Tuning
### What is Fine-Tuning?

Fine-tuning is the process of taking a pre-trained language model and further training it on a smaller, specialized dataset to adapt its behavior, style, or knowledge for specific tasks or domains.

It transforms a general-purpose model into a specialized expert using your data, your style, your rules, and task-specific examples.

### Use Cases

**Example 1: College Support Bot**

*   <b>Base Model:</b> Pretrained chatbot (no institution-specific knowledge)
*   <b>Fine-tuning Input:</b> College website, policies, department details, FAQs
*   <b>Result:</b> Bot knows college rules, schedules, admissions, exams, and hostel info

**Example 2: Exam Prep Assistant**

*  <b>Base Model:</b> Summarizer (can summarize any text, not exam-focused)
*  <b>Fine-tuning Input:</b> Syllabus, textbooks, past question papers, model answers, and topper's notes
*  <b>Result:</b> Generates personalized study notes, highlights key topics, answers subject-specific questions

### What Changes During Fine-Tuning?

An LLM is essentially a neural network made up of parameters (weights). During fine-tuning, we update these weights using our specialized dataset. 

### Applications

*   **Domain Adaptation** — Adapting a general pretrained model to a specific domain like medical, legal, or finance
*   **Task Specialization** — Improving performance on a narrow task such as sentiment analysis, question answering, or named entity recognition
*   **Language/Style Customization** — Fine-tuning to handle specific languages, dialects, or writing styles
*   **Personalization** — Customizing a model to reflect user preferences, vocabulary, or tone
*   **Data Efficiency** — Leveraging a small dataset to teach a large model new knowledge instead of training from scratch
*   **Edge Deployment** — Compressing and fine-tuning smaller models for mobile/IoT use cases

---

## Methods Of Fine-Tuning

1.  **Full Fine-Tuning**
2.  **Parameter Efficient Fine-Tuning (PEFT)** — LoRA, QLoRA, and many more

### Full Fine-Tuning

In full fine-tuning, we update all parameters in the entire model. This gives maximum control but requires a lot of compute power and memory.

### Parameter Efficient Fine-Tuning (PEFT)

Instead of updating all parameters, PEFT methods update only a small subset of parameters, making fine-tuning much faster and cheaper.

** PEFT Methods**

- Selective Method 
- Reparameterization (LoRA / QLoRA) 
- Additive Method 
- Soft Prompting 

---

### Full Fine-Tuning vs PEFT

| Aspect | Full Fine-Tuning | PEFT (e.g., LoRA) |
|---|---|---|
| What's updated | All parameters in the entire network | Only small added layers/matrices |
| Cost | Very expensive | Much cheaper |
| Hardware needed | Multiple high-end GPUs | Single consumer GPU possible |
| Risk | Can ""forget"" general knowledge (catastrophic forgetting) | Preserves base model knowledge |
| When to use | Need maximum domain adaptation | Need efficient, targeted adaptation |

---

## When to Use What?

| Need | Solution |
|---|---|
| Better formatting, tone, or style | Prompt Engineering |
| Access to specific/private/up-to-date documents | RAG |
| Consistent behavior, domain expertise, or learned patterns | Fine-Tuning |
| All of the above | Combine All Three (This is what production systems do!) |

---

## Fine-Tuning a Large Language Model

### What We're Building

**Goal:** Take a base LLM and fine-tune it to respond like a Martian alien — with broken grammar, unique slang, and a consistent alien personality.

**Before Fine-Tuning**

(base model response to ""Hello there""):

> ""Hello! How can I help you today?""

**After Fine-Tuning** (what we want):

> ""Gree-tongz, Terran. You'z a long way from da Blue-Sphere, yez?""

### The Process

1.  Select Base Model
2.  Choose Fine-Tuning Method
3.  Prepare Dataset
4.  Train
5.  Evaluate and Iterate

### Frameworks for Fine-Tuning

Just like we used LangChain as a framework for building agents, we need frameworks for fine-tuning:

*   **Unsloth**
*   **Hugging Face**
*   **Axolotl**
*   **DeepSpeed**
*   **LLaMA Factory**

---

## Steps to Fine-Tune

1.  Install Dependencies and Load Base Model
2.  Test Model Before Fine-Tuning
3.  Apply PEFT (Configure LoRA)
4.  Load and Prepare Dataset
5.  Train and Test the Fine-Tuned Model

## Using Unsloth

Unsloth makes LLM fine-tuning fast and memory-efficient, even on limited hardware.

**Features:**

*   2-5x Faster training
*   70-80% less memory
*   0% Accuracy loss
*   Works on Colab (Free tier)
*   Supports popular models

## Step 1: Install Dependencies and Load Base Model

### Colab Notebook

Open the Google Colab provided below the session. Google Colab provides free Tesla T4 GPU — enough for our fine-tuning.

<MultiLineNote> Need to change resource type to T4 GPU.
</MultiLineNote>
### Install Dependencies

```python
%%capture
!pip install --upgrade --no-cache-dir unsloth unsloth_zoo
!pip install --upgrade --no-deps trl peft accelerate bitsandbytes xformers
```

### Which Models Can We Fine-Tune?

*   Gemma 3 (270M, 1B, 4B, 12B, 27B)
*   Llama 3.2, Llama 3.1, Llama 3
*   Mistral 7B, Mistral
*   Phi-3, Phi-4
*   Qwen 2.5
*   GPT-3.5, GPT-4 (via API only)

**We Choose Gemma 3 270M** — Open-source model by Google, designed for fine-tuning on limited hardware.

### Load the Model Using Unsloth

Unsloth provides a method called `FastModel.from_pretrained()` that loads a model and makes it ready for fine-tuning. It also handles setting up the model efficiently to save memory.

```python
from unsloth import FastModel

model, tokenizer = FastModel.from_pretrained(
    model_name = ""unsloth/gemma-3-270m-it"",
    max_seq_length = 2048,
    load_in_4bit = True,
    load_in_8bit = False,
    full_finetuning = False,
)
```

*   `model` — Loaded Gemma model for fine-tuning
*   `tokenizer` — Converts text ↔ tokens (words/subwords) for the model
*   `max_seq_length = 2048` — The model can read up to 2048 tokens at once
*   `load_in_4bit = True` — Compress the model to use less memory (called quantization — like compressing an image to save space, but for model weights)
*   `load_in_8bit = False` — 8-bit compression is not used
*   `full_finetuning = False` — Tells Unsloth that we don't want to use full fine-tune

## Step 2: Test Model Before Fine-Tuning

Before fine-tuning, let's see how the base model responds. This gives us a baseline to compare against later.

### Understanding Chat Template

Every model has its own chat format with special tokens. `tokenizer.apply_chat_template()` converts our message into the format the model expects.

**Applying Chat Template**

For Gemma 3, the chat template looks like this:

```
<bos><start_of_turn>user
Hello there.<end_of_turn>
<start_of_turn>model...
...
<eos>
```

*   `<bos>` — Beginning of Sequence
*   `<start_of_turn>` — Marks where a message starts
*   `<end_of_turn>` — Marks where a message ends
*   `<eos>` — End of Sequence

### Inference Function

We define a helper function that takes a message, sends it to the model, and prints the response. 

- The `model.generate()` method is what actually produces the model's output.
- `apply_chat_template` This converts our message into the format Model expects


```python
from transformers import TextStreamer

def do_inference(messages, max_new_tokens=128):
    _ = model.generate(
        **tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors=""pt"",
        ).to(""cuda""),
        max_new_tokens=max_new_tokens,
        temperature=1.0,
        top_p=0.95,
        top_k=64,
        streamer=TextStreamer(tokenizer, skip_prompt=True),
    )
```

*   `.to(""cuda"")` — Sends the data to the GPU for fast processing
*   `streamer` — Prints each word as it's generated

<MultiLineNote> The remaining parameters like temperature, top_p, top_k control how the model generates text. We'll understand these in detail in further sessions.
</MultiLineNote> 

### Testing the Model

```python
messages = [{""role"": ""user"", ""content"": ""Hello there.""}]
do_inference(messages)
```

**Expected Output:** ""Hello! How can I help you today?""

The model responds in normal, polished English.

## Step 3: Apply PEFT (Configure LoRA)

Now we need to tell the model which parts to make trainable. We're going with PEFT. Specifically, we'll use LoRA (Low-Rank Adaptation) — the most popular PEFT method.

### How LoRA Works

1.  Freeze all the original model weights (keep them unchanged)
2.  Add small trainable matrices (called adapters) alongside the frozen weights
3.  Train only these small adapter matrices

### Using QLoRA

Since we loaded our model with `load_in_4bit = True`, we're actually using QLoRA (Quantized LoRA) — the model is compressed to 4-bit and then LoRA adapters are applied on top. This means even less memory usage.

### Configure LoRA Using Unsloth

Unsloth provides `FastModel.get_peft_model()` to set up LoRA. This method takes our model and adds small trainable adapters to it.

```python
model = FastModel.get_peft_model(
    model,
    finetune_vision_layers = False,
    finetune_language_layers = True,
    finetune_attention_modules = True,
    finetune_mlp_modules = True,
    r = 8,
    lora_alpha = 8,
    lora_dropout = 0,
    bias = ""none"",
    random_state = 3407,
    use_gradient_checkpointing = ""unsloth"",
)
```

*   `finetune_vision_layers = False` — We are not training image layers (text only)
*   `finetune_language_layers = True` — We train text-related layers
*   `finetune_attention_modules = True` — Train attention heads (how the model focuses on input)
*   `finetune_mlp_modules = True` — Train reasoning layers (Multi Layer Perceptron / Feed Forward Network)
*   `r = 8` — Rank of adapters

<MultiLineNote>We'll understand the remaining parameters in detail in further sessions. </MultiLineNote>
 

## Step 4: Load and Prepare Dataset

### Dataset Selection & Fine-tuning Options

*   Search for datasets for your use case  — personal documents, domain-specific (Healthcare, Law, Finance, E-commerce, Education), or public datasets (Kaggle, Hugging Face, etc.)
*   Adapt relevant dataset — adapt datasets based on your specific use case
*   Prepare (transform/clean, if needed) — some datasets are freely available; others require manual preparation

### Martian NPC Dataset

The `bebechien/MobileGameNPC` dataset provides sample conversations between a player and an alien NPC (a Martian) with a unique speaking style.

The Martian NPC's speaking style:

*   Replaces 's' sounds with 'z' (""is"" → ""iz"")
*   Uses 'da' for 'the'
*   Uses 'diz' for 'this'
*   Includes occasional clicks like *k'tak*
*   Has a consistent alien personality

Sample data: <a href=""https://huggingface.co/datasets/bebechien/MobileGameNPC/viewer/martian/train"" target=""_blank>Huggingface</a>This dataset has only 25 examples — for teaching a consistent speaking style, even a small, high-quality dataset works.

### Load the Dataset

```python
from datasets import load_dataset

dataset = load_dataset(""bebechien/MobileGameNPC"", ""martian"", split=""train"")
```

*   `""bebechien/MobileGameNPC""` — Dataset name
*   `""martian""` — Specific subset/configuration (Martian NPC conversations)
*   `split=""train""` — Loads only the training part of the dataset

### What is Split?

Datasets are usually divided into parts:

*   **train** — Used to train the model
*   **validation** — Used to check performance during training
*   **test** — Used to evaluate final performance

### Inspecting the Data

```python
print(f""Total samples: {len(dataset)}"")
print(f""Columns: {dataset.column_names}"")
print(f""player: {dataset[0]['player']}"")
print(f""alien:  {dataset[0]['alien']}"")
```

### Format for Training

Every model has a specific chat template — a format with special tokens that the model was trained to understand. If we don't follow this format, the model won't learn properly.

**Gemma 3 Chat Template**

```
<bos><start_of_turn>user
Hello there.<end_of_turn>
<start_of_turn>model Gree-tongz, Terran. 
You’z a long way from da Blue-Sphere, yez?<end_of_turn>...<eos>
```


** Loading Gemma 3's Chat Template**


```python
from unsloth.chat_templates import get_chat_template

tokenizer = get_chat_template(tokenizer, chat_template=""gemma-3"")
```

This tells the tokenizer to use Gemma 3's special tokens (`<start_of_turn>`, `<end_of_turn>`, etc.) when formatting conversations.

** Converting Player Pairs to Chat Format**

Our dataset has `player` and `alien` columns. We need to convert them into the chat format.

```python
formatted_texts = []
for i in range(len(dataset)):
    conversation = [
        {""role"": ""user"", ""content"": dataset[i][""player""]},
        {""role"": ""assistant"", ""content"": dataset[i][""alien""]},
    ]
    text = tokenizer.apply_chat_template(
        conversation,
        tokenize=False,
        add_generation_prompt=False
    )
    formatted_texts.append(text)
dataset = dataset.add_column(""text"", formatted_texts)
```

*   For each row, we create a conversation with user (player) and assistant (alien) roles
*   `apply_chat_template` wraps it in Gemma's special tokens format
*   We add the formatted text as a new ""text"" column to our dataset

**Verify the Conversion**

```python
print(""--- After conversion (what model will train on) ---"")
print(dataset[0][""text""])
```

This should show the text wrapped in Gemma's `<start_of_turn>user ... <end_of_turn>` format.

## Step 5: Train and Test the Fine-Tuned Model

### Training the Model Using SFTTrainer

We use Supervised Fine-Tuning Trainer (SFTTrainer) from the Transformer Reinforcement Learning (trl) library to train the model on our dataset until it learns the Martian speaking pattern.

Martian Dataset (Examples) -> SFTTrainer (Fine-Tuning Process) -> Learns Martian Style



```python
from trl import SFTTrainer, SFTConfig
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    args = SFTConfig(
        dataset_text_field = ""text"",
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        num_train_epochs = 30,
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 5,
        optim = ""adamw_8bit"",
        weight_decay = 0.01,
        lr_scheduler_type = ""linear"",
        seed = 3407,
        output_dir = ""outputs"",
        report_to = ""none"",
    ),
)
trainer.train()
```

*   `dataset_text_field = ""text""` — Which column to use from dataset
*   `num_train_epochs = 30` — Number of passes of the entire dataset through the model
*   `learning_rate = 2e-4` — Controls by how much the weights are changed based on the error
*   ` fp16 = not is_bfloat16_supported(), bf16 = is_bfloat16_supported(),` — BFloat16 offers larger range but lower precision than the FloatingPoint16 (when storing weights)
      
<MultiLineNote> The training parameters like learning_rate, gradient_accumulation_steps, warmup_steps, etc. control how the model learns. We'll understand all of these in detail in further sessions.
</MultiLineNote>


### Test After Fine-Tuning

Now the moment of truth! Let's test the fine-tuned model with the same input we used for our baseline:

```python
model = FastModel.for_inference(model)
do_inference([{""role"": ""user"", ""content"": ""Hello there.""}])
```

**Expected Output:** ""Gree-tongz, Terran. You'z a long way from da Blue-Sphere, yez?""

Compare this with the baseline — the model has completely transformed its personality!

---

#### Here is the <a href=""https://colab.research.google.com/drive/1oxvplqO6XdvUwuKmVHSRLsJMoXPJ4kVO#scrollTo=LAiv-wiacKOO"" target=""_blank"" rel=""noopener noreferrer"">Fine-tuning LLMs Final Code (Google Colab)</a>

---

## Try It Yourself

1.  **Fine-tune Stable Diffusion** — Customize image generation for your style, domain, or use case (product photography, art styles, etc.)
2.  **Fine-tune a TTS Model** — Adapt text-to-speech models to generate speech in your own voice with different emotions and tones
3.  **Pick Any Dataset** — Select a dataset from any domain (customer support, medical records, legal documents) and experiment with fine-tuning
4.  **Experiment with Different Models** — Try various base (foundation) models (Llama, Gemma, Mistral) with different datasets and compare results to find the best fit for your use case"

