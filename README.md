# youtube-crawler

### Chức năng 

- Crawl video từ các kênh giáo dục của Youtube
- Gợi ý video phù hợp với người dùng dựa trên phụ đề của mỗi video và tập từ vựng của mỗi người 
- Tìm kiếm video theo từ khóa

### Quá trình thực hiện

- Crawl video và phụ đề của các kênh Youtube (file processor/crawler.py):
    + Lấy channel_id của mỗi kênh dựa trên tên kênh bằng Youtube API
    + Lấy tất cả video của kênh với channel_id tìm được 
    + Với mỗi video, tải phụ đề tiếng Anh của mỗi video bằng Google API
    + Lưu thông tin của các video vào CSDL MongoDB
    
- Xây dựng web server để hiển thị kết quả (folder server/):
    + Người dùng tạo tài khoản, đăng nhập vào website
    + Người dùng nhập tập từ vựng hoặc tải lên file chứa các từ vựng mình đã học ở mục My Vocabulary
    + Trang chủ sẽ hiển thị danh sách các video gợi ý cho người dùng dựa trên tập từ vựng mà người dùng đã nhập, sắp xếp theo thứ tự các từ mới tăng dần
    + Ở mỗi video, người dùng có thể xem thông tin video, tỉ lệ từ mới so với các từ trong video, danh sách các từ mới, các từ trong video, xem chi tiết phụ đề của video
    + Người dùng có thể đánh dấu video đã xem, click Update List để bổ sung các từ trong video đó vào tập từ vựng của mình, sau đó hệ thống sẽ tự động cập nhật để gợi ý video mới
    + Với chức năng tìm kiếm theo phụ đề:
        + Sau khi nhập từ khóa tìm kiếm, website sẽ hiển thị danh sách các video tìm được
        + Tương tự như trang chủ, người dùng có thể xem danh sách các từ mới của mình trong từng video, chi tiết phụ đề với từ khóa tìm kiếm được đánh dấu