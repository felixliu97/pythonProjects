use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    // 1. 使用 Arc (原子引用计数) 让多个线程可以共同拥有这个数字
    // 2. 使用 Mutex (互斥锁) 确保同一时间只有一个线程能修改数字
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for i in 0..10 {
        // 克隆引用，增加计数
        let counter = Arc::clone(&counter);
        
        let handle = thread::spawn(move || {
            // 获取锁，如果失败则 panic
            let mut num = counter.lock().unwrap();
            *num += 1;
            println!("线程 {} 将计数器增加到了: {}", i, *num);
        });
        
        handles.push(handle);
    }

    // 等待所有线程完成
    for handle in handles {
        handle.join().unwrap();
    }

    println!("最终结果: {}", *counter.lock().unwrap());
}