import os
import sys
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox, 
                            QFrame, QSizePolicy, QMenu, QAction)
from PyQt5.QtCore import Qt, QMimeData, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QKeySequence
from PIL import Image
import tempfile
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter

class DropArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        self.label = QLabel("拖拽图片文件到这里或粘贴图片进行转换", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        self.image_preview = QLabel(self)
        self.image_preview.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_preview)
        
        self.file_path = None
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self.file_path = urls[0].toLocalFile()
            self.update_preview()
            
    def update_preview(self):
        if self.file_path and os.path.exists(self.file_path):
            try:
                # 检查是否为ICNS文件
                if self.file_path.lower().endswith('.icns'):
                    # 使用PIL处理ICNS文件
                    try:
                        img = Image.open(self.file_path)
                        # 创建临时PNG文件用于预览
                        temp_png = os.path.join(tempfile.gettempdir(), "icns_preview_temp.png")
                        img.save(temp_png, format='PNG')
                        pixmap = QPixmap(temp_png)
                    except Exception as e:
                        self.label.setText(f"ICNS预览错误: {str(e)}")
                        self.image_preview.clear()
                        return
                else:
                    pixmap = QPixmap(self.file_path)
                
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_preview.setPixmap(pixmap)
                    self.label.setText(os.path.basename(self.file_path))
                else:
                    self.label.setText("无法预览图片")
                    self.image_preview.clear()
            except Exception as e:
                self.label.setText(f"预览错误: {str(e)}")
                self.image_preview.clear()
                
    def contextMenuEvent(self, event):
        """处理右键菜单事件"""
        context_menu = QMenu(self)
        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.paste_from_clipboard)
        context_menu.addAction(paste_action)
        context_menu.exec_(event.globalPos())
        
    def paste_from_clipboard(self):
        """从剪贴板粘贴图像"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, "pasted_image.png")
            pixmap = clipboard.pixmap()
            pixmap.save(temp_file, "PNG")
            self.file_path = temp_file
            self.update_preview()
            # 更新主窗口的源文件输入框
            if self.parent() and hasattr(self.parent(), 'source_edit'):
                self.parent().source_edit.setText(self.file_path)
        elif mime_data.hasUrls():
            urls = mime_data.urls()
            if urls and urls[0].isLocalFile():
                self.file_path = urls[0].toLocalFile()
                self.update_preview()
                # 更新主窗口的源文件输入框
                if self.parent() and hasattr(self.parent(), 'source_edit'):
                    self.parent().source_edit.setText(self.file_path)
    
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            self.paste_from_clipboard()
        else:
            super().keyPressEvent(event)

class IconConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # 自动填写输出文件夹为当前用户的桌面
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.output_edit.setText(desktop_path)
        
    def initUI(self):
        self.setWindowTitle('图标格式互转工具')
        self.setGeometry(100, 100, 600, 400)
        
        # 使窗口在屏幕中央显示
        self.center()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部文件选择部分
        file_layout = QVBoxLayout()
        
        source_layout = QHBoxLayout()
        source_label = QLabel("源文件:")
        self.source_edit = QLineEdit()
        source_browse = QPushButton("浏览...")
        source_browse.clicked.connect(self.browse_source)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(source_browse)
        
        output_layout = QHBoxLayout()
        output_label = QLabel("输出文件夹:")
        self.output_edit = QLineEdit()
        output_browse = QPushButton("浏览...")
        output_browse.clicked.connect(self.browse_output)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(output_browse)
        
        file_layout.addLayout(source_layout)
        file_layout.addLayout(output_layout)
        
        main_layout.addLayout(file_layout)
        
        # 中间按钮部分
        button_layout = QHBoxLayout()
        
        self.ico_button = QPushButton("转换为ICO")
        self.icns_button = QPushButton("转换为ICNS")
        self.png_button = QPushButton("转换为PNG")
        self.favicon_button = QPushButton("转换为Favicon")
        self.svg_button = QPushButton("转换为SVG")
        
        self.ico_button.clicked.connect(lambda: self.convert_image("ico"))
        self.icns_button.clicked.connect(lambda: self.convert_image("icns"))
        self.png_button.clicked.connect(lambda: self.convert_image("png"))
        self.favicon_button.clicked.connect(lambda: self.convert_image("favicon"))
        self.svg_button.clicked.connect(lambda: self.convert_image("svg"))
        
        button_layout.addWidget(self.ico_button)
        button_layout.addWidget(self.icns_button)
        button_layout.addWidget(self.png_button)
        button_layout.addWidget(self.favicon_button)
        button_layout.addWidget(self.svg_button)
        
        main_layout.addLayout(button_layout)
        
        # 底部拖拽区域
        self.drop_area = DropArea()
        self.drop_area.setFocusPolicy(Qt.StrongFocus)
        main_layout.addWidget(self.drop_area)
        
        # 初始化状态栏
        self.statusBar().showMessage('准备就绪')
        
    def center(self):
        # 获取屏幕几何信息
        screen = QApplication.desktop().screenGeometry()
        # 获取窗口几何信息
        size = self.geometry()
        # 计算窗口居中时左上角的坐标
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        # 移动窗口到计算出的位置
        self.move(x, y)

    def keyPressEvent(self, event):
        # 允许按Ctrl+V直接粘贴到应用程序中
        if event.matches(QKeySequence.Paste):
            self.drop_area.setFocus()
            self.drop_area.keyPressEvent(event)
        else:
            super().keyPressEvent(event)
            
    def dragEnterEvent(self, event):
        # 允许拖拽到整个窗口
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        # 处理拖拽到窗口的事件
        self.drop_area.dropEvent(event)
        self.source_edit.setText(self.drop_area.file_path)
        
    def browse_source(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择源文件", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.ico *.icns *.svg);;所有文件 (*)"
        )
        if file_path:
            self.source_edit.setText(file_path)
            self.drop_area.file_path = file_path
            self.drop_area.update_preview()
            
    def browse_output(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder_path:
            self.output_edit.setText(folder_path)
            
    def get_source_file(self):
        # 优先使用拖拽区域的文件
        if self.drop_area.file_path and os.path.exists(self.drop_area.file_path):
            return self.drop_area.file_path
        
        # 其次使用源文件输入框的文件
        source_path = self.source_edit.text()
        if source_path and os.path.exists(source_path):
            return source_path
            
        return None
        
    def get_output_folder(self):
        output_folder = self.output_edit.text()
        if not output_folder:
            # 如果没有指定输出文件夹，使用源文件所在的文件夹
            source_file = self.get_source_file()
            if source_file:
                output_folder = os.path.dirname(source_file)
            else:
                output_folder = os.getcwd()
                
        # 确保输出文件夹存在
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        return output_folder
    
    # 添加 SVG 转 PNG 的辅助函数
    def svg_to_png(self, svg_path, png_path, width=None, height=None):
        """将 SVG 转换为 PNG，使用 Qt 的 SVG 渲染器"""
        # 创建 SVG 渲染器
        renderer = QSvgRenderer(svg_path)
        
        # 获取 SVG 的默认大小
        default_size = renderer.defaultSize()
        
        # 如果指定了尺寸，则使用指定的尺寸
        if width and height:
            size_w, size_h = width, height
        else:
            size_w, size_h = default_size.width(), default_size.height()
        
        # 创建图像
        image = QImage(size_w, size_h, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # 创建画家
        painter = QPainter(image)
        
        # 渲染 SVG
        renderer.render(painter)
        painter.end()
        
        # 保存为 PNG
        image.save(png_path)
        
        return png_path
        
    def convert_image(self, target_format):
        source_file = self.get_source_file()
        if not source_file:
            QMessageBox.warning(self, "警告", "请先选择或拖入源文件")
            return
            
        output_folder = self.get_output_folder()
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        
        self.statusBar().showMessage(f'正在转换为{target_format.upper()}格式...')
        QApplication.processEvents()  # 确保UI更新
        
        try:
            # 如果源文件是ICNS，先转换为临时PNG文件
            temp_png = None
            if source_file.lower().endswith('.icns'):
                try:
                    img = Image.open(source_file)
                    temp_png = os.path.join(tempfile.gettempdir(), f"{base_name}_temp.png")
                    img.save(temp_png, format='PNG')
                    source_file = temp_png
                except Exception as e:
                    raise Exception(f"无法处理ICNS文件: {str(e)}")
            
            if target_format == "ico":
                output_file = self.convert_to_ico(source_file, output_folder, base_name)
            elif target_format == "icns":
                output_file = self.convert_to_icns(source_file, output_folder, base_name)
            elif target_format == "png":
                output_file = self.convert_to_png(source_file, output_folder, base_name)
            elif target_format == "favicon":
                output_file = self.convert_to_favicon(source_file, output_folder, base_name)
            elif target_format == "svg":
                output_file = self.convert_to_svg(source_file, output_folder, base_name)
                
            self.statusBar().showMessage(f'已成功转换为{target_format.upper()}格式: {output_file}')
            QMessageBox.information(self, "成功", f"已成功转换为{target_format.upper()}格式\n保存在: {output_file}")
            
            # 清理临时文件
            if temp_png and os.path.exists(temp_png):
                os.remove(temp_png)
                
        except Exception as e:
            self.statusBar().showMessage(f'转换失败: {str(e)}')
            QMessageBox.critical(self, "错误", f"转换失败: {str(e)}")
            
            # 确保清理临时文件
            if temp_png and os.path.exists(temp_png):
                os.remove(temp_png)
        
    def convert_to_ico(self, source_file, output_folder, base_name):
        output_file = os.path.join(output_folder, f"{base_name}.ico")
        
        # 如果源文件是SVG，先转换为PNG
        if source_file.lower().endswith('.svg'):
            temp_png = os.path.join(tempfile.gettempdir(), f"{base_name}_temp.png")
            # 使用新的 svg_to_png 方法替代 cairosvg
            self.svg_to_png(source_file, temp_png)
            source_file = temp_png
        
        img = Image.open(source_file)
        
        # ICO格式支持多种尺寸，我们创建常用的几种尺寸
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(output_file, format='ICO', sizes=sizes)
        
        return output_file
        
    # 修改其他转换方法，让它们返回输出文件路径
    # 在导入部分不需要修改，PyQt5和PIL在ARM macOS上都可以正常工作
    
    # 在IconConverter类的convert_to_icns方法中需要确保iconutil命令在ARM macOS上正确执行
    def convert_to_icns(self, source_file, output_folder, base_name):
        output_file = os.path.join(output_folder, f"{base_name}.icns")
        
        # 如果源文件是SVG，先转换为PNG
        if source_file.lower().endswith('.svg'):
            temp_png = os.path.join(tempfile.gettempdir(), f"{base_name}_temp.png")
            # 使用新的 svg_to_png 方法替代 cairosvg
            self.svg_to_png(source_file, temp_png)
            source_file = temp_png
            
        # 创建临时目录
        temp_dir = os.path.join(tempfile.gettempdir(), "icns_conversion")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        try:
            # ICNS需要特定尺寸的图像
            sizes = {
                "16x16": "16x16.png",
                "32x32": "32x32.png",
                "64x64": "64x64.png",
                "128x128": "128x128.png",
                "256x256": "256x256.png",
                "512x512": "512x512.png",
                "1024x1024": "1024x1024.png"
            }
            
            img = Image.open(source_file)
            
            # 创建各种尺寸的图像
            for size, filename in sizes.items():
                width, height = map(int, size.split('x'))
                resized_img = img.resize((width, height), Image.LANCZOS)
                resized_img.save(os.path.join(temp_dir, filename))
                
            # 使用iconutil命令创建icns文件 (在macOS上有效，包括ARM架构)
            if sys.platform == 'darwin':
                iconset_dir = os.path.join(temp_dir, "icon.iconset")
                if not os.path.exists(iconset_dir):
                    os.makedirs(iconset_dir)
                    
                # 按照Apple的命名规范创建iconset
                icon_name_map = {
                    "16x16": "icon_16x16.png",
                    "32x32": "icon_32x32.png",
                    "64x64": "icon_64x64.png",
                    "128x128": "icon_128x128.png",
                    "256x256": "icon_256x256.png",
                    "512x512": "icon_512x512.png",
                    "1024x1024": "icon_1024x1024.png"
                }
                
                for size, src_filename in sizes.items():
                    dst_filename = icon_name_map[size]
                    shutil.copy(
                        os.path.join(temp_dir, src_filename),
                        os.path.join(iconset_dir, dst_filename)
                    )
                    
                # 使用subprocess代替os.system以获得更好的错误处理
                import subprocess
                try:
                    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", output_file], 
                                   check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    raise Exception(f"iconutil命令执行失败: {e.stderr.decode('utf-8')}")
                    
                return output_file
            else:
                # 在非macOS系统上，我们只能提供PNG文
                output_dir = os.path.join(output_folder, f"{base_name}_icns")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
                for size, filename in sizes.items():
                    shutil.copy(
                        os.path.join(temp_dir, filename),
                        os.path.join(output_dir, filename)
                    )
                    
                QMessageBox.information(
                    self, 
                    "ICNS转换", 
                    f"由于Windows不支持直接创建ICNS文件，已在{output_dir}创建了所需的PNG文件集合。"
                )
                return output_dir  # 返回包含PNG文件集合的目录
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    def convert_to_png(self, source_file, output_folder, base_name):
        output_file = os.path.join(output_folder, f"{base_name}.png")
        
        # 如果源文件是SVG，使用 svg_to_png 方法替代 cairosvg
        if source_file.lower().endswith('.svg'):
            self.svg_to_png(source_file, output_file)
        else:
            img = Image.open(source_file)
            # 如果图像有透明通道，保留它
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img.save(output_file, format='PNG')
            else:
                # 转换为RGB模式
                img = img.convert('RGB')
                img.save(output_file, format='PNG')
        
        return output_file
                
    def convert_to_favicon(self, source_file, output_folder, base_name):
        # 创建favicon.ico文件（包含多种尺寸）
        output_file = os.path.join(output_folder, f"{base_name}_favicon.ico")
        
        # 如果源文件是SVG，先转换为PNG
        if source_file.lower().endswith('.svg'):
            temp_png = os.path.join(tempfile.gettempdir(), f"{base_name}_temp.png")
            # 使用新的 svg_to_png 方法替代 cairosvg
            self.svg_to_png(source_file, temp_png)
            source_file = temp_png
        
        img = Image.open(source_file)
        
        # Favicon通常包含这些尺寸
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        img.save(output_file, format='ICO', sizes=sizes)
        
        # 同时创建一个PNG格式的favicon
        png_output = os.path.join(output_folder, f"{base_name}_favicon.png")
        favicon_img = img.resize((32, 32), Image.LANCZOS)
        favicon_img.save(png_output, format='PNG')
        
        return output_file
        
    def convert_to_svg(self, source_file, output_folder, base_name):
        output_file = os.path.join(output_folder, f"{base_name}.svg")
        
        # 如果源文件已经是SVG，直接复制
        if source_file.lower().endswith('.svg'):
            shutil.copy(source_file, output_file)
            return output_file
            
        # 注意：从位图转换为SVG是一个复杂的过程，需要矢量化
        # 这里我们只是提供一个简单的SVG包装
        img = Image.open(source_file)
        width, height = img.size
        
        # 将图像保存为PNG以便嵌入
        temp_png = os.path.join(tempfile.gettempdir(), f"{base_name}_temp.png")
        img.save(temp_png, format='PNG')
        
        # 读取PNG文件并转换为base64
        import base64
        with open(temp_png, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 创建一个简单的SVG文件，嵌入PNG图像
        svg_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image width="{width}" height="{height}" xlink:href="data:image/png;base64,{encoded_string}"/>
</svg>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        # 删除临时文件
        if os.path.exists(temp_png):
            os.remove(temp_png)
        
        return output_file

def main():
    app = QApplication(sys.argv)
    window = IconConverter()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
