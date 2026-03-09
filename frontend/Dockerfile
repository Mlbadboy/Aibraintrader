# Stage 1: Build the React application
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Build arguments for environment variables
ARG VITE_API_BASE_URL=""
ARG VITE_AUTH_API_URL="/auth"
ARG VITE_GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID_HERE"

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_AUTH_API_URL=$VITE_AUTH_API_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

# Copy the rest of the application code
COPY . .

# Build the application
# We use build-arg for the API URL during build time if needed, 
# although we've set up runtime env vars in App.jsx
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the built assets to the Nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy a custom nginx config for the frontend if needed
# For now, standard alpine nginx is fine as we have a main gateway

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
