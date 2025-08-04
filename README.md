# Findajob Project

Welcome to the Findajob project!

## Getting Started

To get started with this project, follow these steps:

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/smaltravel/findajob.git
   cd findajob
   ```

2. **Create and Activate a Virtual Environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install Requirements:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the LinkedIn Spider:**

   ```bash
   scrapy crawl linkedin -a keywords='<Position Description>' -a location='<Search Location>'
   ```

## Project Structure

The project is structured as follows:

- `findajob/`: Main package directory.
  - `items.py`: Defines data items for the project.
  - `middlewares.py`: Contains middlewares if any.
  - `pipelines.py`: Processes scraped items, stores them in database etc.
  - `settings.py`: Project settings and configuration.
  - `spiders/`: Directory containing spider classes.
    - `linkedin_api_spider.py`: Example spider for scraping LinkedIn data.

## Configuration

Ensure that your project settings (`settings.py`) are properly configured according to your requirements.

### Running the Spider

To run a specific spider, use the following command:

```bash
scrapy crawl <spider_name>
```

For example:

```bash
scrapy crawl linkedin
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear, descriptive messages.
4. Push to your forked repository.
5. Submit a pull request.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
