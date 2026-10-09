"""Reviewed upstream sources and learning contracts (no generated/synthetic data)."""

LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
VERIFIED_ON = "2026-10-09"


def spec(uci_id, slug, name, domain, citation, doi, table, rows, tasks, questions, guidance):
    return {
        "uci_id": uci_id, "slug": slug, "name": name, "domain": domain,
        "source_url": f"https://archive.ics.uci.edu/dataset/{uci_id}/{slug}",
        "download_url": f"https://archive.ics.uci.edu/static/public/{uci_id}/{slug.replace('+', '%2B')}.zip",
        "citation": citation, "doi": f"https://doi.org/{doi}",
        "primary_table": table, "expected_rows": rows, "tasks": tasks,
        "questions": questions, "guidance": guidance,
    }


SOURCES = {
    "online_retail": spec(352, "online+retail", "Online Retail", "retail_analytics",
        "Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository.",
        "10.24432/C5BW33", "invoice_lines", 541909,
        ["data_quality", "sql", "rfm_segmentation", "market_basket", "cohort_analysis"],
        ["Giá trị giao dịch có dấu thay đổi thế nào theo tháng và quốc gia?",
         "RFM của khách hàng thay đổi thế nào khi xử lý hoàn/hủy và dòng trùng?",
         "Sản phẩm nào thường xuất hiện cùng trong một hóa đơn bán hàng?"],
        ["Giữ toàn bộ 541.909 dòng, cả null, số lượng/giá âm và dòng trùng. Đây là dữ liệu để học xử lý chất lượng.",
         "InvoiceNo không phải khóa dòng. StockCode có mã dịch vụ/điều chỉnh; Description có thể thay đổi cho cùng mã.",
         "line_amount_gbp = quantity × unit_price_gbp; đây là giá trị có dấu theo nguồn, chưa phải doanh thu kế toán đã đối soát.",
         "Mart tháng dùng tất cả dòng, không loại trùng. Tháng 12/2011 chỉ có đến ngày 09 nên không so tăng trưởng nguyên tháng.",
         "RFM cần khách hàng có ID, quy tắc hoàn/hủy và trùng được công bố. Chốt ngày quan sát rồi chỉ dùng lịch sử trước ngày đó.",
         "Market basket thường giới hạn hóa đơn không hủy, quantity > 0, unit_price_gbp > 0; công bố cách xử lý mã phi sản phẩm.",
         "Cohort chỉ đo khách hàng quan sát được trong snapshot, không có lịch sử trước 12/2010 hoặc sau 09/12/2011."]),
    "bike_sharing": spec(275, "bike+sharing+dataset", "Bike Sharing", "mobility_forecasting",
        "Fanaee-T, H. (2013). Bike Sharing [Dataset]. UCI Machine Learning Repository.",
        "10.24432/C5W894", "hourly_rentals", 17379,
        ["time_series", "regression", "sql"],
        ["Nhu cầu xe đạp khác nhau thế nào theo giờ, ngày làm việc và mùa?",
         "Baseline mùa vụ và mô hình hồi quy dự báo nhu cầu tốt đến mức nào?"],
        ["2011–2012, Capital Bikeshare. File hour.csv thực tế có 17.379 dòng dù trang nguồn ghi 17.389; dùng số đo từ file.",
         "day.csv có 731 ngày là aggregate cùng hệ thống. Không nối dọc ngày và giờ rồi cộng lượt thuê.",
         "Không có đủ mọi giờ trong lịch. Không tự điền giờ vắng bằng zero; resample và công bố chính sách missing trước khi tạo lag.",
         "Dự báo rental_count: loại casual_count và registered_count vì tổng hai biến bằng target.",
         "Chia train/validation/test theo thời gian, rolling-origin backtest; tạo lag bằng shift trước khi rolling.",
         "Thời tiết đo trong giờ chỉ dùng nếu đã biết ở thời điểm dự báo; bài dự báo tương lai cần forecast thời tiết hoặc loại biến này.",
         "Các biến nhiệt độ, độ ẩm, gió được chuẩn hóa ở nguồn. Giữ đơn vị normalized và không tự giải chuẩn hóa aggregate ngày.",
         "Readme.txt gốc và trang UCI hiện tại ghi nhãn season/chuẩn hóa nhiệt độ khác nhau. Giữ mã season số, không tự gán tên mùa hoặc đổi về Celsius khi chưa thống nhất định nghĩa."]),
    "bank_marketing": spec(222, "bank+marketing", "Bank Marketing (Additional Full)", "marketing_classification",
        "Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing [Dataset]. UCI Machine Learning Repository.",
        "10.24432/C5K306", "campaign_contacts", 41188,
        ["classification", "imbalanced_learning", "categorical_encoding"],
        ["Tỷ lệ đăng ký tiền gửi khác nhau thế nào theo kênh và kết quả chiến dịch trước?",
         "Mô hình trước cuộc gọi có cải thiện PR-AUC và recall so với baseline không?"],
        ["Chỉ dùng bank-additional-full.csv, không ghép sample 10% hay phiên bản bank-full cũ vào cùng dữ liệu.",
         "Một dòng là quan sát chiến dịch theo nguồn, không phải khách hàng duy nhất; không có ID để bảo đảm tách khách hàng.",
         "duration chỉ biết sau cuộc gọi. Loại duration khỏi mô hình dùng trước cuộc gọi; đây là leakage quan trọng.",
         "unknown là category được giữ nguyên, pdays = 999 nghĩa là chưa liên hệ trước, không phải 999 ngày thông thường.",
         "Nguồn sắp xếp theo thời gian 05/2008–11/2010 nhưng không có ngày đầy đủ. Giữ source_row, có thể holdout theo thứ tự; không dựng ngày giả từ month.",
         "Fit encoder, imputer, scaler và resampling chỉ trên train. Dùng PR-AUC, precision/recall, calibration và threshold theo bài toán."]),
    "student_performance": spec(320, "student+performance", "Student Performance", "education_analytics",
        "Cortez, P. (2008). Student Performance [Dataset]. UCI Machine Learning Repository.",
        "10.24432/C5TG7T", "subject_results", 1044,
        ["regression", "classification", "grouped_validation"],
        ["Phân phối điểm cuối kỳ khác nhau thế nào giữa môn Toán và tiếng Bồ Đào Nha?",
         "Hiệu quả dự báo G3 trước học kỳ và sau G2 khác nhau ra sao?"],
        ["Gộp 395 dòng Toán và 649 dòng tiếng Bồ Đào Nha; 1.044 là số quan sát môn học, không phải 1.044 học sinh riêng biệt.",
         "Không có student ID. Các thuộc tính ghép trong tài liệu nguồn chỉ là heuristic và có thể va chạm, không tạo khóa học sinh giả.",
         "Nên thực hành từng môn riêng. Nếu gộp hai môn, xác định nhóm cùng học sinh theo hướng dẫn nguồn rồi audit sự mơ hồ trước group split.",
         "Dự báo từ đầu kỳ phải loại g1, g2 và biến chỉ biết sau thời điểm dự báo. Bài sau G2 có thể dùng g1/g2 nếu công bố thời điểm.",
         "Biến dạng thang thứ bậc 1–5 cần giữ nghĩa ordinal; association không chứng minh tác động nhân quả."]),
    "wine_quality": spec(186, "wine+quality", "Wine Quality (Red + White)", "quality_regression",
        "Cortez, P., Cerdeira, A., Almeida, F., Matos, T., & Reis, J. (2009). Wine Quality [Dataset]. UCI Machine Learning Repository.",
        "10.24432/C56S3T", "wine_samples", 6497,
        ["regression", "ordinal_classification", "feature_selection"],
        ["Những đặc tính hóa lý nào liên quan đến quality?",
         "Sai số dự báo và mất cân bằng điểm quality khác nhau thế nào giữa rượu đỏ và trắng?"],
        ["Gộp 1.599 mẫu đỏ và 4.898 mẫu trắng, giữ wine_type và mọi dòng trùng để người học quyết định cách xử lý.",
         "quality là điểm ordinal 0–10. Không tự nhị phân hóa good/bad; nếu dùng classification phải công bố ngưỡng và phân phối lớp.",
         "Giữ các dòng có vector feature giống nhau trong cùng split để hạn chế contamination; fit scaling chỉ trên train.",
         "Không có brand, giá, giống nho hoặc khóa mẫu tự nhiên; record_id chỉ là khóa kỹ thuật của snapshot."]),
    "energy_efficiency": spec(242, "energy+efficiency", "Energy Efficiency", "building_energy",
        "Tsanas, A., & Xifara, A. (2012). Energy Efficiency [Dataset]. UCI Machine Learning Repository.",
        "10.24432/C51307", "building_simulations", 768,
        ["multioutput_regression", "grouped_validation", "feature_importance"],
        ["Hình học công trình và diện tích kính liên quan thế nào đến heating/cooling load?",
         "Mô hình dự báo có khái quát tốt khi giữ riêng một nhóm hình dạng công trình không?"],
        ["768 cấu hình mô phỏng Ecotect từ 12 hình dạng công trình, không phải đo tiêu thụ điện từ 768 công trình thực tế.",
         "Hai target là heating_load và cooling_load. Loại cả hai khỏi X cho bài multi-output; không dùng một target để dự báo target còn lại trừ khi nó thực sự đã biết.",
         "orientation và glazing_area_distribution là mã category, không phải đại lượng liên tục.",
         "Đánh giá bằng group holdout theo hình dạng (relative_compactness/surface_area/wall_area/roof_area/overall_height), so với random split.",
         "File Excel có thể có dòng/cột trống cuối bảng. Chỉ đọc 10 cột X1–X8, Y1–Y2 và bỏ dòng hoàn toàn trống; phải còn đúng 768 dòng."]),
}

SOURCES["bike_sharing"]["publication_citation"] = (
    "Fanaee-T, H., & Gama, J. (2013). Event labeling combining ensemble detectors and background knowledge. "
    "Progress in Artificial Intelligence. https://doi.org/10.1007/s13748-013-0040-3 (requested in the source Readme).")
SOURCES["wine_quality"]["publication_citation"] = (
    "Cortez, P., Cerdeira, A., Almeida, F., Matos, T., & Reis, J. (2009). Modeling wine preferences by data mining "
    "from physicochemical properties. Decision Support Systems, 47(4), 547–553. "
    "https://doi.org/10.1016/j.dss.2009.05.016 (requested in winequality.names).")


def descriptions(text):
    return dict(line.split("|", 1) for line in text.strip().splitlines())


COMMON = descriptions("""
record_id|Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể.
source_file|Tên file gốc bên trong archive nguồn.
source_row|Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header.
""")

COLUMNS = {
    "online_retail": descriptions("""
invoice_no|Mã hóa đơn; bắt đầu bằng C/c chỉ hủy theo nguồn. Không duy nhất tại grain dòng.
stock_code|Mã sản phẩm hoặc mã dịch vụ/điều chỉnh, giữ dạng text.
description|Mô tả sản phẩm gốc; cho phép null, không tự điền hoặc chuẩn hóa nội dung.
quantity|Số lượng có dấu từ nguồn; gồm giá trị âm.
invoice_date|Thời điểm hóa đơn, timezone không được nguồn công bố.
unit_price_gbp|Giá một đơn vị theo bảng nguồn, GBP; giữ cả zero và âm.
customer_id|Mã khách hàng dạng text; null nghĩa là nguồn không có ID, không phải một khách hàng chung.
country|Quốc gia theo dữ liệu nguồn.
is_cancellation|Cờ derived khi invoice_no bắt đầu bằng C/c.
line_amount_gbp|quantity × unit_price_gbp, giá trị có dấu của dòng theo nguồn, GBP.
"""),
    "bike_sharing": descriptions("""
instant|Chỉ số dòng gốc; không dùng làm predictor.
date|Ngày quan sát 2011–2012.
season|Mã mùa 1–4 giữ nguyên. Readme gốc ghi 1 springer/2 summer/3 fall/4 winter, trang UCI ghi 1 winter/2 spring/3 summer/4 fall; nhãn chưa được thống nhất.
year_code|Mã năm: 0 = 2011, 1 = 2012.
month|Tháng 1–12.
hour|Giờ 0–23; chỉ có ở hourly_rentals.
holiday|Ngày nghỉ theo nguồn: 0/1.
weekday|Ngày trong tuần, 0 Sunday đến 6 Saturday.
working_day|1 khi không phải cuối tuần/ngày nghỉ, còn lại 0.
weather_situation|Mã 1 clear, 2 mist/cloudy, 3 light snow/rain, 4 heavy rain/snow/fog; chi tiết trong Readme.txt gốc.
temperature_normalized|Nhiệt độ đã chuẩn hóa ở nguồn, giữ thang normalized.
feels_like_normalized|Nhiệt độ cảm nhận đã chuẩn hóa ở nguồn.
humidity_normalized|Độ ẩm chia cho 100 ở nguồn.
windspeed_normalized|Tốc độ gió chia cho 67 ở nguồn.
casual_count|Lượt thuê khách vãng lai; thành phần của target nên không dùng khi dự báo tổng.
registered_count|Lượt thuê khách đăng ký; thành phần của target nên không dùng khi dự báo tổng.
rental_count|Tổng lượt thuê, bằng casual_count + registered_count.
timestamp|date + hour ở bảng giờ, timezone không được nguồn công bố.
"""),
    "bank_marketing": descriptions("""
age|Tuổi theo nguồn, năm.
job|Nghề nghiệp dạng category, có unknown.
marital|Tình trạng hôn nhân; divorced gồm ly hôn/góa theo nguồn.
education|Trình độ học vấn dạng category.
default|Có tín dụng vỡ nợ: yes/no/unknown.
housing|Có khoản vay nhà: yes/no/unknown.
loan|Có khoản vay cá nhân: yes/no/unknown.
contact|Kênh liên hệ cellular/telephone.
month|Tháng của lần liên hệ cuối; không có năm đầy đủ.
day_of_week|Ngày trong tuần của lần liên hệ cuối.
duration|Thời lượng cuộc gọi cuối, giây. Chỉ biết sau cuộc gọi, loại khỏi dự báo trước cuộc gọi.
campaign|Số lần liên hệ trong chiến dịch hiện tại, gồm lần cuối.
pdays|Số ngày kể từ chiến dịch trước; 999 là chưa từng liên hệ, giữ sentinel.
previous|Số lần liên hệ trước chiến dịch hiện tại.
poutcome|Kết quả chiến dịch trước: failure/nonexistent/success.
emp_var_rate|Employment variation rate, chỉ số theo quý từ nguồn.
cons_price_idx|Consumer price index, chỉ số theo tháng từ nguồn.
cons_conf_idx|Consumer confidence index, chỉ số theo tháng từ nguồn.
euribor3m|Euribor kỳ hạn 3 tháng, chỉ số theo ngày từ nguồn.
nr_employed|Number of employees, chỉ số theo quý từ nguồn; giữ đơn vị/thang gốc.
subscribed|Target: đăng ký tiền gửi, yes/no; đổi tên từ y, không đổi nhãn.
"""),
    "student_performance": descriptions("""
subject|Môn học: mathematics hoặc portuguese; derived từ file nguồn.
school|Trường: GP hoặc MS.
sex|Mã giới tính F/M trong nguồn.
age|Tuổi, năm.
address|Loại nơi ở: U urban, R rural.
famsize|Quy mô gia đình: LE3 <=3, GT3 >3 người.
pstatus|Tình trạng sống chung của bố mẹ: T together, A apart.
medu|Học vấn mẹ: 0 none, 1 primary, 2 lớp 5–9, 3 secondary, 4 higher.
fedu|Học vấn bố: cùng mã 0–4 như medu.
mjob|Nghề mẹ: teacher/health/services/at_home/other.
fjob|Nghề bố: teacher/health/services/at_home/other.
reason|Lý do chọn trường: home/reputation/course/other.
guardian|Người giám hộ: mother/father/other.
traveltime|Thời gian đi học: 1 <15 phút, 2 15–30 phút, 3 30–60 phút, 4 >60 phút.
studytime|Học mỗi tuần: 1 <2 giờ, 2 2–5 giờ, 3 5–10 giờ, 4 >10 giờ.
failures|Số lần trượt môn trước đó; giữ mã nguồn, xem student.txt.
schoolsup|Hỗ trợ giáo dục thêm: yes/no.
famsup|Hỗ trợ học tập từ gia đình: yes/no.
paid|Học thêm có trả phí cho môn học: yes/no.
activities|Hoạt động ngoại khóa: yes/no.
nursery|Đã học mẫu giáo: yes/no.
higher|Muốn học bậc cao hơn: yes/no.
internet|Có Internet ở nhà: yes/no.
romantic|Có quan hệ tình cảm: yes/no.
famrel|Chất lượng quan hệ gia đình: ordinal 1 rất xấu đến 5 rất tốt.
freetime|Thời gian rảnh sau học: ordinal 1 rất ít đến 5 rất nhiều.
goout|Đi chơi với bạn: ordinal 1 rất ít đến 5 rất nhiều.
dalc|Tiêu thụ rượu ngày làm việc: ordinal 1 rất ít đến 5 rất nhiều.
walc|Tiêu thụ rượu cuối tuần: ordinal 1 rất ít đến 5 rất nhiều.
health|Tình trạng sức khỏe tự báo cáo: ordinal 1 rất xấu đến 5 rất tốt.
absences|Số buổi vắng học theo nguồn.
g1|Điểm kỳ 1, 0–20; chỉ dùng nếu đã biết ở thời điểm dự báo.
g2|Điểm kỳ 2, 0–20; chỉ dùng nếu đã biết ở thời điểm dự báo.
g3|Target: điểm cuối kỳ, 0–20.
"""),
    "wine_quality": descriptions("""
wine_type|red/white, derived từ file nguồn.
fixed_acidity|Fixed acidity, giữ thang số gốc; archive không khai báo đơn vị.
volatile_acidity|Volatile acidity, giữ thang số gốc.
citric_acid|Citric acid, giữ thang số gốc.
residual_sugar|Residual sugar, giữ thang số gốc.
chlorides|Chlorides, giữ thang số gốc.
free_sulfur_dioxide|Free sulfur dioxide, giữ thang số gốc.
total_sulfur_dioxide|Total sulfur dioxide, giữ thang số gốc.
density|Density, giữ thang số gốc.
ph|pH của mẫu; không có đơn vị.
sulphates|Sulphates, giữ thang số gốc.
alcohol|Alcohol, giữ thang số gốc.
quality|Target: điểm chất lượng sensory, ordinal 0–10.
"""),
    "energy_efficiency": descriptions("""
relative_compactness|X1: Relative compactness, giữ thang nguồn.
surface_area|X2: Surface area, giữ thang nguồn.
wall_area|X3: Wall area, giữ thang nguồn.
roof_area|X4: Roof area, giữ thang nguồn.
overall_height|X5: Overall height, giữ thang nguồn.
orientation|X6: Mã orientation 2–5, categorical.
glazing_area|X7: Glazing area, giữ thang nguồn.
glazing_area_distribution|X8: Mã glazing area distribution 0–5, categorical.
heating_load|Y1: Target heating load từ mô phỏng, giữ thang nguồn; không giả định kWh.
cooling_load|Y2: Target cooling load từ mô phỏng, giữ thang nguồn; không giả định kWh.
"""),
}

TARGETS = {"bike_sharing": ["rental_count"], "bank_marketing": ["subscribed"],
           "student_performance": ["g3"], "wine_quality": ["quality"],
           "energy_efficiency": ["heating_load", "cooling_load"]}
GRAINS = {
    "invoice_lines": "Một dòng dữ liệu giao dịch nguồn, bao gồm điều chỉnh, hoàn/hủy và trùng.",
    "hourly_rentals": "Một giờ quan sát trong hệ thống thuê xe.",
    "daily_rentals": "Một ngày aggregate chính thức từ nguồn, không phải bản ghi giờ mới.",
    "campaign_contacts": "Một quan sát chiến dịch từ bank-additional-full.csv, không có khóa khách hàng.",
    "subject_results": "Một quan sát học sinh × môn trong file gốc; không có ID học sinh đáng tin cậy.",
    "wine_samples": "Một dòng mẫu rượu trong file gốc; các vector số có thể trùng.",
    "building_simulations": "Một cấu hình công trình trong mô phỏng nguồn.",
}
