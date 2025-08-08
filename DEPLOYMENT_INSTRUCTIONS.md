# Apply these changes to your docker-compose.yml on Ubuntu:

# 1. Remove the 'version: 3.8' line at the top
# 2. Update the frontend service ports to include port 80:
#    ports:
#      - "80:80"
#      - "3000:3000"
# 3. Remove the entire nginx service section

# Here's what your docker-compose.yml should look like:
