
echo $CLOUDFUNCTION_RESOURCE_ID \
&& echo $PROJECT_ID \
&& echo $LOCATION_ID \
&& \
gcloud477 functions deploy $CLOUDFUNCTION_RESOURCE_ID \
--gen2 \
--project $PROJECT_ID \
--runtime=nodejs22 \
--trigger-http \
--allow-unauthenticated \
--region $LOCATION_ID