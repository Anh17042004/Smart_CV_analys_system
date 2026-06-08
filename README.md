Sau này, khi bạn có sửa đổi code trên máy tính của mình và muốn cập nhật lên môi trường chạy thật, bạn chỉ cần mở terminal và chạy 3 lệnh rất đơn giản:

bash
# 1. Commit các thay đổi của bạn
git add .
git commit -m "mô tả thay đổi của bạn"
# 2. Cập nhật Frontend lên Vercel (và sao lưu code lên GitHub)
git push origin main
# 3. Cập nhật Backend lên Hugging Face Space
git push hf $(git subtree split --prefix=backend main):main --force