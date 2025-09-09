FROM python:3.11-slim

WORKDIR /app

# Install Streamlit and dependencies
RUN pip install streamlit plotly pandas requests

# Create .streamlit directory
RUN mkdir -p .streamlit

# Copy Streamlit app files
COPY web/frontend/ .

# Expose Streamlit port
EXPOSE 8501

# Set environment variable for Streamlit
ENV STREAMLIT_SERVER_HEADLESS=true

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
