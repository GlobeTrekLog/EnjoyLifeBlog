---
layout:     post
title:      MSI-HOWTO翻译简介
subtitle:   
date:       2024-5-24
author:     EnjoyLife
header-img: img/post-bg-coffee.jpg
catalog: 	true
tags:
    - PCIe
    - MSI
---



原文地址：

https://www.kernel.org/doc/Documentation/PCI/MSI-HOWTO.txt





### 总结内容：

这篇指南介绍了消息信号中断（MSI）的基础知识，MSI相对于传统中断机制的优势，如何修改驱动程序以使用MSI或MSI-X，以及设备不支持MSI时的一些基本诊断方法。

MSI通过设备向一个特殊地址写入信息，来向CPU发送中断信号。MSI具有比传统针脚中断更多的优势，比如不共享中断线、避免数据同步问题、支持更多的中断向量等。指南还详细介绍了在Linux系统中如何配置和使用MSI，以及一些常见问题的解决方法。



### 翻译全文：

#### 消息信号中断（MSI）驱动指南

**作者**：Tom L Nguyen (tom.l.nguyen@intel.com)  
**日期**：2003年10月3日  
**修订**：2004年2月12日 Martine Silbermann (Martine.Silbermann@hp.com)  
**修订**：2004年6月25日 Tom L Nguyen  
**修订**：2008年7月9日 Matthew Wilcox (willy@linux.intel.com)  
**版权**：2003, 2008 Intel Corporation

#### 1. 关于本指南

本指南介绍了消息信号中断（MSI）的基础知识，MSI相对于传统中断机制的优势，如何修改驱动程序以使用MSI或MSI-X，以及一些基本的诊断方法以应对设备不支持MSI的情况。

#### 2. 什么是MSI？

消息信号中断是一种通过设备向一个特殊地址写入数据来引发中断的机制。MSI功能最早在PCI 2.2中定义，并在PCI 3.0中得到增强，以允许每个中断单独屏蔽。MSI-X功能也在PCI 3.0中引入，支持比MSI更多的中断，并允许独立配置中断。

设备可以同时支持MSI和MSI-X，但只能启用其中一个。

#### 3. 为什么使用MSI？

使用MSI相对于传统针脚中断有三个主要优势：
- **独立性**：针脚中断通常在多个设备之间共享，内核必须调用与中断相关的每个中断处理程序，导致系统性能下降。而MSI从不共享，因此不存在这个问题。
- **数据同步**：使用针脚中断时，可能出现中断信号到达CPU前数据尚未写入内存的情况。MSI避免了这个问题，因为中断生成的写操作不能超越数据写入操作。
- **多中断支持**：PCI设备每个功能只能支持一个针脚中断，而MSI可以支持多个中断，允许每个中断专用于不同的目的，提高中断处理效率。

#### 4. 如何使用MSI

PCI设备初始化时默认使用针脚中断。设备驱动程序需要设置设备以使用MSI或MSI-X。并非所有机器都正确支持MSI，对于这些机器，API会失败，设备将继续使用针脚中断。

##### 4.1 包含内核对MSI的支持

内核必须启用CONFIG_PCI_MSI选项以支持MSI或MSI-X。这一选项仅在某些架构上可用，并且可能依赖于其他选项的启用。

##### 4.2 使用MSI

大部分工作由PCI层完成，驱动程序只需请求PCI层为设备设置MSI功能。

使用以下函数自动分配MSI或MSI-X中断向量：
```c
int pci_alloc_irq_vectors(struct pci_dev *dev, unsigned int min_vecs, unsigned int max_vecs, unsigned int flags);
```
这个函数为PCI设备分配最多max_vecs个中断向量，返回分配的向量数量或一个负错误码。flags参数用于指定设备和驱动程序可以使用的中断类型。

使用以下函数获取传递给`request_irq()`和`free_irq()`的Linux IRQ号及向量：
```c
int pci_irq_vector(struct pci_dev *dev, unsigned int nr);
```
在移除设备前释放任何分配的资源：
```c
void pci_free_irq_vectors(struct pci_dev *dev);
```

如果设备同时支持MSI-X和MSI，这个API会优先使用MSI-X。MSI-X支持1到2048个中断，而MSI最多支持32个中断，并且必须是2的幂。

典型用法是尽可能多地分配向量：
```c
nvec = pci_alloc_irq_vectors(pdev, 1, nvec, PCI_IRQ_ALL_TYPES);
if (nvec < 0)
    goto out_err;
```

一些设备可能不支持使用传统针脚中断，这种情况下驱动程序可以指定只接受MSI或MSI-X：
```c
nvec = pci_alloc_irq_vectors(pdev, 1, nvec, PCI_IRQ_MSI | PCI_IRQ_MSIX);
if (nvec < 0)
    goto out_err;
```

##### 4.3 传统API

以下旧的API不应在新代码中使用：
```c
pci_enable_msi();      /* 不推荐 */
pci_disable_msi();     /* 不推荐 */
pci_enable_msix_range(); /* 不推荐 */
pci_enable_msix_exact(); /* 不推荐 */
pci_disable_msix();    /* 不推荐 */
```

还提供了用于获取支持的MSI或MSI-X向量数量的API：`pci_msi_vec_count()`和`pci_msix_vec_count()`。一般应避免使用这些API，而是让`pci_alloc_irq_vectors()`自动调整向量数量。

##### 4.4 使用MSI时的注意事项

###### 4.4.1 自旋锁

大多数设备驱动程序在中断处理程序中都有一个每设备自旋锁。对于针脚中断或单一MSI，不需要禁用中断（Linux保证同一中断不会重新进入）。如果设备使用多个中断，驱动程序必须在持有锁时禁用中断，以避免死锁。

##### 4.5 如何判断设备是否启用了MSI/MSI-X

使用`lspci -v`命令（以root身份运行）可以查看设备是否具有"MSI"、"Message Signalled Interrupts"或"MSI-X"功能。这些功能各有一个'Enable'标志，显示为"+"（启用）或"-"（禁用）。

#### 5. MSI的特殊情况

一些PCI芯片组或设备不支持MSI。PCI栈提供了三种禁用MSI的方法：
1. 全局禁用
2. 禁用所有在特定桥下的设备
3. 禁用单个设备

##### 5.1 全局禁用MSI

某些主机芯片组不支持MSI。如果制造商在ACPI FADT表中指明这一点，Linux会自动禁用MSI。如果没有此信息，需要手动检测。在`drivers/pci/quirks.c`文件中可以找到这些信息。

如果您的主板存在MSI问题，可以在内核命令行传递`pci=nomsi`禁用所有设备的MSI。

##### 5.2 禁用桥下的MSI

某些PCI桥无法正确路由MSI。在这种情况下，必须禁用桥下所有设备的MSI。

一些桥允许通过修改PCI配置空间中的位来启用MSI，尤其是Hypertransport芯片组（如nVidia nForce和Serverworks HT2000）。Linux大部分情况下会自动启用这些桥的MSI。

##### 5.3 禁用单个设备的MSI

一些设备的MSI实现存在问题，通常在设备驱动程序中处理，但有时需要通过特定的方法处理。某些驱动程序有禁用MSI的选项，但这不是好习惯。

##### 5.4 查找设备禁用MSI的原因

可以通过检查dmesg日志确定MSI是否已启用，并检查内核配置文件中的CONFIG_PCI_MSI选项是否已启用。

使用`lspci -t`命令查看设备的桥列表，读取`/sys/bus/pci/devices/*/msi_bus`文件可以查看MSI是否启用。如果在任何桥的`msi_bus`文件中看到0，说明MSI被禁用。

还可以查看设备驱动程序是否支持MSI，比如驱动程序中是否包含对`pci_irq_alloc_vectors()`的调用及其参数。

通过这些步骤，可以有效了解和诊断MSI的使用情况和问题。