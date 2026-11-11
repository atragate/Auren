#include <efi.h>
#include <efilib.h>
EFI_STATUS efi_main(EFI_HANDLE h,EFI_SYSTEM_TABLE *t) { return 0; }
int main(void) {
 UINTN tools[24];
 for(unsigned i=0;i<24;i++)tools[i]=0xabcdef;
 SetMem(tools,sizeof tools,0);
 for(unsigned i=0;i<24;i++)if(tools[i]!=0)return 1;
 return 0;
}
