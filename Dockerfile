FROM jamieleecho/coco-dev:latest

# Store stuff in a semi-reasonable spot
RUN rm -rf coco-tools && mkdir /root/coco-tools
WORKDIR /root/coco-tools
ENV PYTHONPATH=/root/coco-tools/src

# Setup requirements
# Install requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy source files
COPY setup.py ./
COPY README.md ./
COPY tests ./tests
COPY coco ./coco

# Install coco-tools
RUN python3 setup.py install
