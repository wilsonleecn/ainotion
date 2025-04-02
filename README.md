# ainotion
Put Notion files to Vector DB

docker build -t ainotion:latest .   

docker run -it --rm -v $(pwd):/home/work/ ainotion:latest bash

