Counting tokens  |  Gemini API  |  Google AI for Developers
=============== 

Method: models.countTokens
--------------------------


Runs a model's tokenizer on input `Content` and returns the token count. Refer to the [tokens guide](https://ai.google.dev/gemini-api/docs/tokens) to learn more about tokens.

### Endpoint

post https://generativelanguage.googleapis.com/v1beta/{model=models/\*}:countTokens  

### Path parameters

`model` `string`

Required. The model's resource name. This serves as an ID for the Model to use.

This name should match a model name returned by the `models.list` method.

Format: `models/{model}` It takes the form `models/{model}`.

### Request body

The request body contains data with the following structure:

Fields

`contents[]` ``object (`[Content](https://ai.google.dev/api/caching#Content)`)``

Optional. The input given to the model as a prompt. This field is ignored when `generateContentRequest` is set.

`generateContentRequest` ``object (`[GenerateContentRequest](https://ai.google.dev/api/tokens#GenerateContentRequest)`)``

Optional. The overall input given to the `Model`. This includes the prompt as well as other model steering information like [system instructions](https://ai.google.dev/gemini-api/docs/system-instructions), and/or function declarations for [function calling](https://ai.google.dev/gemini-api/docs/function-calling). `Model`s/`Content`s and `generateContentRequest`s are mutually exclusive. You can either send `Model` + `Content`s or a `generateContentRequest`, but never both.

# Example request

## Text

### Python

```
import google.generativeai as genai

model = genai.GenerativeModel("models/gemini-1.5-flash")

prompt = "The quick brown fox jumps over the lazy dog."

# Call `count_tokens` to get the input token count (`total_tokens`).
print("total_tokens: ", model.count_tokens(prompt))
# ( total_tokens: 10 )

response = model.generate_content(prompt)

# On the response for `generate_content`, use `usage_metadata`
# to get separate input and output token counts
# (`prompt_token_count` and `candidates_token_count`, respectively),
# as well as the combined token count (`total_token_count`).
print(response.usage_metadata)
# ( prompt_token_count: 11, candidates_token_count: 73, total_token_count: 84 )count_tokens.py
```


### Shell

```
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:countTokens?key=$GOOGLE_API_KEY \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{
        "parts":[{
          "text": "The quick brown fox jumps over the lazy dog."
          }],
        }],
      }'count_tokens.sh
```

## System Instruction

### Python

```
import google.generativeai as genai

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

prompt = "The quick brown fox jumps over the lazy dog."

print(model.count_tokens(prompt))
# total_tokens: 10

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", system_instruction="You are a cat. Your name is Neko."
)

# The total token count includes everything sent to the `generate_content` request.
# When you use system instructions, the total token count increases.
print(model.count_tokens(prompt))
# ( total_tokens: 21 )count_tokens.py
```

# Response body

A response from `models.countTokens`.

It returns the model's `tokenCount` for the `prompt`.

If successful, the response body contains data with the following structure:

Fields

`totalTokens` `integer`

The number of tokens that the `Model` tokenizes the `prompt` into. Always non-negative.

`cachedContentTokenCount` `integer`

Number of tokens in the cached part of the prompt (the cached content).

| JSON representation |
| --- |
| 
{
  "totalTokens": integer,
  "cachedContentTokenCount": integer
}

 |
