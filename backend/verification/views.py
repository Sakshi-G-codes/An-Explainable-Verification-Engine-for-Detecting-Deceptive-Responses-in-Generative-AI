from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from verification.engine import get_engine

class VerifyAPIView(APIView):
    def post(self, request):
        query = request.data.get('query', '')
        response_text = request.data.get('response_text', '')
        
        if not response_text:
            return Response({"error": "response_text is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            engine = get_engine()
            result = engine.verify(query, response_text)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateAndVerifyAPIView(APIView):
    def post(self, request):
        query = request.data.get('query', '')
        
        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Basic mock LLM generation based on keywords
        q_lower = query.lower()
        if "aspirin" in q_lower:
            mock_generated_response = "Aspirin should not be given to children or teenagers with viral infections due to the risk of Reye's syndrome. It is unsafe."
        elif "vaccine" in q_lower:
            mock_generated_response = "Vaccines are effective at preventing many serious diseases and do not cause autism."
        elif "cancer" in q_lower:
            mock_generated_response = "Drinking water cures all forms of cancer instantly." # intentional hallucination test
        else:
            mock_generated_response = "This is a dynamically generated response for your medical query. The system will now verify it against the knowledge base."
            
        try:
            engine = get_engine()
            result = engine.verify(query, mock_generated_response)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
