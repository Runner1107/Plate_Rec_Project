import onnxruntime
import copy
from image_processing import four_point_transform, get_split_merge, get_plate_result, detect_pre_precessing, post_precessing

def rec_plate(outputs,img0,session_rec):  #识别车牌
    dict_list=[]
    for output in outputs:
        result_dict={}
        rect=output[:4].tolist()
        land_marks = output[5:13].reshape(4,2)
        roi_img = four_point_transform(img0,land_marks)
        label = int(output[-1])
        score = output[4]
        if label==1:  #代表是双层车牌
            roi_img = get_split_merge(roi_img)
        plate_no,plate_color = get_plate_result(roi_img,session_rec)
        result_dict['rect']=rect
        result_dict['landmarks']=land_marks.tolist()
        result_dict['plate_no']=plate_no
        result_dict['roi_height']=roi_img.shape[0]
        result_dict['plate_color']=plate_color
        dict_list.append(result_dict)
    return dict_list

class plate_detect_rec:
    def __init__(self,):
        # self.detect_model = r'weights\best_blaze_face.onnx'
        # self.rec_model= r"weights\plate_rec_color_0820.onnx"
        providers =  ['CPUExecutionProvider']
        self.session_detect = onnxruntime.InferenceSession(r'weights/best_blaze_face.onnx', providers=providers )
        self.session_rec = onnxruntime.InferenceSession(r"weights/plate_rec_color_0820.onnx", providers=providers )
        
    def __call__(self,img,img_size):
        img0 = copy.deepcopy(img)
        img,r,left,top = detect_pre_precessing(img,img_size) #检测前处理
        # print(img.shape)
        
        # img=np.concatenate((img,img))
        # print(img)
        y_onnx = self.session_detect.run([self.session_detect.get_outputs()[0].name], {self.session_detect.get_inputs()[0].name: img})[0]
        outputs = post_precessing(y_onnx,r,left,top) #检测后处理
        result_list=rec_plate(outputs,img0,self.session_rec)
        return result_list,img0

def plate_recognition_thread(cap, plate_queue, img_size):
    plateRec = plate_detect_rec()
    while True:
        ret_val, img = cap.read()
        if ret_val:
            result, img0 = plateRec(img, img_size)
            if result:
                # 将识别结果和图像放入队列
                plate_queue.put((result, img0))