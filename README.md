# youtube-crawler

### Chức năng 

- Crawl video từ các kênh giáo dục của Youtube
- Gợi ý video phù hợp với người dùng dựa trên phụ đề của mỗi video và tập từ vựng của mỗi người 
- Hiển thị chủ đề, các từ quan trọng, word cloud của mỗi video

### Quá trình thực hiện

- Crawl video và phụ đề của các kênh Youtube (file processor/crawler.py):
    + Lấy channel_id của mỗi kênh dựa trên tên kênh bằng Youtube API
    + Lấy tất cả video của kênh với channel_id tìm được 
    + Với mỗi video, tải phụ đề tiếng Anh của mỗi video bằng Google API
    + Lưu thông tin của các video vào CSDL MongoDB

- Phân tích phụ đề của các video (file processor/analyzer.py)
    + Tokenize phụ đề 
    + Tìm chủ đề, vẽ word cloud
    
- Xây dựng web server để hiển thị kết quả (folder server/):
    