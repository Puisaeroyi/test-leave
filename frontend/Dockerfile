# Frontend Dockerfile - Development Mode with Hot Reload
FROM node:20-alpine

# Set work directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy project
COPY . .

# Expose port
EXPOSE 5173

# Run dev server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
