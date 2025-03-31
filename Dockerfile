FROM jamieleecho/coco-dev:latest

# Store stuff in a semi-reasonable spot
RUN rm -rf coco-tools && mkdir /root/coco-tools
WORKDIR /root/coco-tools
ENV PYTHONPATH=/root/coco-tools/src

# Install requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy source files
COPY coco ./coco
COPY Makefile .
COPY README.md ./
COPY tests ./tests

# Install coco-tools
RUN make build-dist && \
  make install
