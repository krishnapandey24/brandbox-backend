### ENDPOINTS

**POST** `http://127.0.0.1:5000/products`

**Headers:**
- `Content-Type`: `application/json`

**Body:** `JSON`

```json
{
  "name": "name_tM01",
  "description": "description_WW24",
  "price": 577,
  "stock_quantity": 704,
  "category_id": 60
}
```
**GET** `http://127.0.0.1:5000/products`

**Headers:**
- `Content-Type`: `application/json`


**POST** `http://127.0.0.1:5000/category`

**Headers:**
- `Content-Type`: `application/json`

**Body:** `JSON`

```json
{
  "category_name": "NEW",
  "category_description": "hello"
}
```

### Draft

**POST** `http://127.0.0.1:5000/login`

**Headers:**
- `Content-Type`: `application/json`

**Body:** `JSON`

```json
{
  "provider": "google",
  "email": "krishna@gmail.com",
  "name": "krishna"
}
```


### Draft

**GET** `http://localhost:5000/products?category_id=1&page=1&per_page=1&sort_by=sales&sort_order=desc&include_out_of_stock=false`

**Query Params:**
- `category_id`: `1`
- `page`: `1`
- `per_page`: `1`
- `sort_by`: `sales`
- `sort_order`: `desc`
- `include_out_of_stock`: `false`

**Headers:**
- `Content-Type`: `multipart/form-data`

