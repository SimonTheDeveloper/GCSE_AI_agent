FROM node:18

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build the React app
RUN npm run build

# Serve the build with a simple static server
RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]