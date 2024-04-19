# shared
Stores All Business Logic for the Angies Job Board Backend



Patterns of this repository


You'll see some common file names in each of the contexts in this repo

The contexts may be embedded into each other if they are expected to be stored as children
For instance, you'll find the Resume context under a user because it is a direct relationship

BUT, you'll find the Application context at the "Parent" level because it is a 
shared entity between a user and a company/job.


Each context will have files matching this pattern, some may have all of these and 
others may only have a portion of these files depending on what is needed

models
enumerations
search
repository
usecase
async_service


docker run -e ARANGO_NO_AUTH=1 -p 8529:8529 -d --name arangodb-instance arangodb/arangodb:latest



Full Flow example - 


Company creates and posts a job

Candidate views job (job is included in search)
Candidate Clicks job (job details are retrieved but user not is recruiter)
Candidate applies


Company views
 